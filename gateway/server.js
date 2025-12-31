require('dotenv').config();
const express = require('express');
const amqp = require('amqplib');
const { auth } = require('express-oauth2-jwt-bearer');
const multer = require('multer');
const { v4: uuidv4 } = require('uuid');
const path = require('path');

const app = express();
const RABBIT_URL = 'amqp://rabbitmq';

const checkJwt = auth({
  audience: process.env.AUTH0_AUDIENCE,
  issuerBaseURL: `https://${process.env.AUTH0_DOMAIN}/`,
  tokenSigningAlg: 'RS256'
});

app.use(express.json());

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, '/shared_data/uploads'); 
  },
  filename: (req, file, cb) => {
    const uniqueName = uuidv4() + path.extname(file.originalname); 
    cb(null, uniqueName);
  }
});

const upload = multer({ storage });

app.get('/test-queue', checkJwt, async (req, res) => {
    console.log('Authorization header:', req.headers.authorization); //debug
    try {
        const conn = await amqp.connect(RABBIT_URL);
        const channel = await conn.createChannel();
        const queue = 'health_check';

        const userId = req.auth.payload.sub;

        const payload = {
            sender: 'gateway-service',
            content: 'ping',
            timestamp: new Date(),
            user: {
                sub: userId
            }
        };

        await channel.assertQueue(queue, { durable: false });
        channel.sendToQueue(queue, Buffer.from(JSON.stringify(payload)));

        console.log(` [User B] Sent secure msg for: ${userId}`);

        await channel.close();
        await conn.close();

        res.json({ status: 'success', message: 'Secure message sent', user: userId });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: err.message });
    }
});


// file uploads
app.post('/upload', checkJwt, upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    // RabbitMQ connection
    const conn = await amqp.connect(RABBIT_URL);
    const channel = await conn.createChannel();
    const queue = 'task_queue';

    const taskId = uuidv4();

    const payload = {
      task_id: taskId,
      user_id: req.auth.payload.sub,       
      file_path: req.file.path,           
      original_name: req.file.originalname,
      status: 'pending'
    };

    await channel.assertQueue(queue, { durable: true }); 
    channel.sendToQueue(queue, Buffer.from(JSON.stringify(payload)), {
      persistent: true                  
    });

    console.log(` [User B] Uploaded & Queued: ${taskId}`);

    await channel.close();
    await conn.close();

    res.json({
      status: 'queued',
      task_id: taskId,
      message: 'File uploaded for processing'
    });

  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

app.use((err, req, res, next) => {
  console.error('Auth error:', err);

  if (
    err.status === 401 ||
    err.name === 'UnauthorizedError' ||
    err.name === 'InvalidRequestError' ||
    err.code === 'invalid_token' ||
    err.code === 'invalid_request'
  ) {
    return res.status(401).json({ error: 'Missing or Invalid Token' });
  }

  next(err);
});

app.listen(3000, () => console.log('Gateway running on port 3000'));