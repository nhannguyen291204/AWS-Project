import 'dotenv/config';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient } from '@aws-sdk/lib-dynamodb';
import { S3Client } from '@aws-sdk/client-s3';

const required = ['AWS_REGION', 'S3_BUCKET_NAME', 'LOGIN_TABLE_NAME', 'MUSIC_TABLE_NAME', 'SUBSCRIPTION_TABLE_NAME'];

export function assertConfiguration() {
  const missing = required.filter((name) => !process.env[name]);
  if (missing.length) throw new Error(`Missing environment variables: ${missing.join(', ')}`);
}

const options = { region: process.env.AWS_REGION || 'us-east-1' };
if (process.env.AWS_ACCESS_KEY_ID) {
  options.credentials = {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
    sessionToken: process.env.AWS_SESSION_TOKEN
  };
}

export const dynamo = new DynamoDBClient(options);
export const db = DynamoDBDocumentClient.from(dynamo, {
  marshallOptions: { removeUndefinedValues: true }
});
export const s3 = new S3Client(options);
export const tables = {
  login: process.env.LOGIN_TABLE_NAME || 'login',
  music: process.env.MUSIC_TABLE_NAME || 'music',
  subscription: process.env.SUBSCRIPTION_TABLE_NAME || 'subscription'
};
export const bucket = process.env.S3_BUCKET_NAME;
