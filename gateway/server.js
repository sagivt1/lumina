const express = require('express');
const amqp = require('amqplib');
const app = express();

const RABBIT_URL = 'amqp://rabbitmq';

app.get('/test-queue', async (req, res) => {
    try {
        const conn = await amqp.connect(RABBIT_URL);
        const channel = await conn.createChannel();
        const queue = 'health_check';

        const payload = {
            sender: 'gateway-service',
            content: 'ping',
            timestamp: new Date()
        };

        // Ensure queue exists
        await channel.assertQueue(queue, { durable: false });

        // Send message
        channel.sendToQueue(queue, Buffer.from(JSON.stringify(payload)));

        console.log(` [User B] Sent: ${JSON.stringify(payload)}`);

        // Clean up
        await channel.close();
        await conn.close();

        res.json({ status: 'success', message: 'Sent to RabbitMQ' });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: err.message });
    }
});

app.listen(3000, () => console.log('Gateway running on port 3000'));