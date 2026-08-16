import 'dotenv/config';
import express from 'express';
import session from 'express-session';
import { GetCommand, PutCommand, DeleteCommand, QueryCommand, ScanCommand } from '@aws-sdk/lib-dynamodb';
import { GetObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { assertConfiguration, bucket, db, s3, tables } from './aws.js';

import { fileURLToPath } from 'url';

assertConfiguration();
const app = express();
app.set('view engine', 'ejs');
app.set('views', fileURLToPath(new URL('./views', import.meta.url)));
app.use(express.urlencoded({ extended: false }));
app.use(express.static('public'));
app.use(session({ secret: process.env.SESSION_SECRET || 'change-me', resave: false, saveUninitialized: false, cookie: { httpOnly: true, sameSite: 'lax' } }));

const signedImage = async (item) => ({ ...item, image: await getSignedUrl(s3, new GetObjectCommand({ Bucket: bucket, Key: item.image_key }), { expiresIn: 3600 }) });
const requireLogin = (req, res, next) => req.session.user ? next() : res.redirect('/');

app.get('/', (req, res) => res.render('login', { message: '', email: '' }));
app.post('/login', async (req, res, next) => {
  try {
    const email = req.body.email?.trim().toLowerCase();
    const { Item } = await db.send(new GetCommand({ TableName: tables.login, Key: { email } }));
    if (!Item || Item.password !== req.body.password) return res.status(401).render('login', { message: 'email or password is invalid', email });
    req.session.user = { email: Item.email, userName: Item.user_name };
    res.redirect('/main');
  } catch (error) { next(error); }
});

app.get('/register', (req, res) => res.render('register', { message: '', values: {} }));
app.post('/register', async (req, res, next) => {
  try {
    const values = { email: req.body.email?.trim().toLowerCase(), user_name: req.body.user_name?.trim(), password: req.body.password };
    if (!values.email || !values.user_name || !values.password) return res.status(400).render('register', { message: 'All fields are required', values });
    const { Item } = await db.send(new GetCommand({ TableName: tables.login, Key: { email: values.email } }));
    if (Item) return res.status(409).render('register', { message: 'The email already exists', values });
    await db.send(new PutCommand({ TableName: tables.login, Item: values }));
    res.redirect('/?registered=1');
  } catch (error) { next(error); }
});

app.get('/main', requireLogin, async (req, res, next) => {
  try {
    const response = await db.send(new QueryCommand({ TableName: tables.subscription, KeyConditionExpression: 'email = :email', ExpressionAttributeValues: { ':email': req.session.user.email } }));
    res.render('main', { user: req.session.user, subscriptions: await Promise.all((response.Items || []).map(signedImage)), results: null, filters: {}, message: '' });
  } catch (error) { next(error); }
});

app.post('/query', requireLogin, async (req, res, next) => {
  try {
    const filters = Object.fromEntries(['title', 'artist', 'year'].map((key) => [key, req.body[key]?.trim() || '']));
    const terms = Object.entries(filters).filter(([, value]) => value);
    const music = await db.send(new ScanCommand({ TableName: tables.music }));
    const matches = (music.Items || []).filter((song) => terms.every(([key, value]) => String(song[key]).toLowerCase().includes(value.toLowerCase())));
    const subscriptions = await db.send(new QueryCommand({ TableName: tables.subscription, KeyConditionExpression: 'email = :email', ExpressionAttributeValues: { ':email': req.session.user.email } }));
    res.render('main', { user: req.session.user, subscriptions: await Promise.all((subscriptions.Items || []).map(signedImage)), results: await Promise.all(matches.map(signedImage)), filters, message: matches.length ? '' : 'No result is retrieved. Please query again' });
  } catch (error) { next(error); }
});

app.post('/subscribe', requireLogin, async (req, res, next) => {
  try {
    const { Item } = await db.send(new GetCommand({ TableName: tables.music, Key: { title: req.body.title } }));
    if (Item) await db.send(new PutCommand({ TableName: tables.subscription, Item: { email: req.session.user.email, ...Item } }));
    res.redirect('/main');
  } catch (error) { next(error); }
});
app.post('/remove', requireLogin, async (req, res, next) => {
  try { await db.send(new DeleteCommand({ TableName: tables.subscription, Key: { email: req.session.user.email, title: req.body.title } })); res.redirect('/main'); }
  catch (error) { next(error); }
});
app.post('/logout', (req, res) => req.session.destroy(() => res.redirect('/')));
app.use((error, req, res, next) => { console.error(error); res.status(500).send('Unexpected server error. Check the EC2 application logs.'); });
app.listen(Number(process.env.PORT || 3000), () => console.log(`Music subscription app listening on port ${process.env.PORT || 3000}`));
