require('dotenv').config();
const express = require('express');
const amqp = require('amqplib');
const { auth } = require('express-oauth2-jwt-bearer');
const app = express();

const RABBIT_URL = 'amqp://rabbitmq';

const checkJwt = auth({
  audience: process.env.AUTH0_AUDIENCE,
  issuerBaseURL: `https://${process.env.AUTH0_DOMAIN}/`,
  tokenSigningAlg: 'RS256'
});

app.use(express.json());

app.get('/test-queue', checkJwt, async (req, res) => {
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

app.use((err, req, res, next) => {
  if (err.name === 'UnauthorizedError') {
    res.status(401).json({ error: 'Missing or Invalid Token' });
  } else {
    next(err);
  }
});

app.listen(3000, () => console.log('Gateway running on port 3000'));