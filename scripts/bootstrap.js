import 'dotenv/config';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { CreateTableCommand, DescribeTableCommand, waitUntilTableExists } from '@aws-sdk/client-dynamodb';
import { BatchWriteCommand } from '@aws-sdk/lib-dynamodb';
import { HeadBucketCommand, PutObjectCommand } from '@aws-sdk/client-s3';
import { assertConfiguration, bucket, db, dynamo, s3, tables } from '../aws.js';

assertConfiguration();
const rawDb = db.send.bind(db);

async function ensureTable(TableName, keySchema) {
  try {
    await rawDb(new DescribeTableCommand({ TableName }));
    console.log(`Table ${TableName} already exists.`);
    return;
  } catch (error) {
    if (error.name !== 'ResourceNotFoundException') throw error;
  }
  await rawDb(new CreateTableCommand({
    TableName, BillingMode: 'PAY_PER_REQUEST',
    AttributeDefinitions: keySchema.attributes,
    KeySchema: keySchema.keys
  }));
  await waitUntilTableExists({ client: dynamo, maxWaitTime: 120 }, { TableName });
  console.log(`Created table ${TableName}.`);
}

async function batchPut(TableName, records) {
  for (let index = 0; index < records.length; index += 25) {
    await db.send(new BatchWriteCommand({ RequestItems: { [TableName]: records.slice(index, index + 25).map((Item) => ({ PutRequest: { Item } })) } }));
  }
}

function passwordFor(index) { return `${index}${(index + 1) % 10}${(index + 2) % 10}${(index + 3) % 10}${(index + 4) % 10}${(index + 5) % 10}`; }
function imageKey(url) { return `artist-images/${createHash('sha256').update(url).digest('hex')}.jpg`; }

await ensureTable(tables.login, { attributes: [{ AttributeName: 'email', AttributeType: 'S' }], keys: [{ AttributeName: 'email', KeyType: 'HASH' }] });
await ensureTable(tables.music, { attributes: [{ AttributeName: 'title', AttributeType: 'S' }], keys: [{ AttributeName: 'title', KeyType: 'HASH' }] });
await ensureTable(tables.subscription, { attributes: [{ AttributeName: 'email', AttributeType: 'S' }, { AttributeName: 'title', AttributeType: 'S' }], keys: [{ AttributeName: 'email', KeyType: 'HASH' }, { AttributeName: 'title', KeyType: 'RANGE' }] });

await s3.send(new HeadBucketCommand({ Bucket: bucket }));
const songs = JSON.parse(await readFile(new URL('../a2.json', import.meta.url))).songs;
const studentId = process.env.STUDENT_ID;
const firstName = process.env.FIRST_NAME;
const lastName = process.env.LAST_NAME;
if (!studentId || !firstName || !lastName) throw new Error('Set STUDENT_ID, FIRST_NAME and LAST_NAME in .env before bootstrapping.');

await batchPut(tables.login, Array.from({ length: 10 }, (_, index) => ({
  email: `${studentId}${index}@student.rmit.edu.au`, user_name: `${firstName} ${lastName}${index}`, password: passwordFor(index)
})));

const music = songs.map((song) => ({ ...song, image_key: imageKey(song.img_url) }));
await batchPut(tables.music, music);

for (const song of music) {
  const response = await fetch(song.img_url);
  if (!response.ok) throw new Error(`Could not download image for ${song.title}: ${response.status}`);
  await s3.send(new PutObjectCommand({ Bucket: bucket, Key: song.image_key, Body: Buffer.from(await response.arrayBuffer()), ContentType: response.headers.get('content-type') || 'image/jpeg' }));
}
console.log(`Loaded ${music.length} songs and uploaded their artist images to S3.`);
