const express = require("express");
const http = require("http");
const { Server } = require("socket.io");
const redis = require("redis");
const cors = require("cors");

const app = express();
app.use(cors());
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: ["http://localhost:3000", "http://localhost:3001"],
    methods: ["GET", "POST"],
    credentials: true,
  },
});

// Redis client
const redisClient = redis.createClient({ url: "redis://localhost:6379" });
redisClient.connect().then(() => {
  console.log("Connected to Redis");
  redisClient.subscribe("notifications", (message) => {
    try {
      const notification = JSON.parse(message);
      io.to(`user_${notification.user}`).emit("new_notification", notification);
    } catch (err) {
      console.error("Redis message error:", err);
    }
  });
});

// Socket.IO connection
io.on("connection", (socket) => {
  console.log("Client connected");

  socket.on("join", (userId) => {
    socket.join(`user_${userId}`);
    console.log(`User ${userId} joined notification room`);
  });

  socket.on("mark_read", (notificationId) => {
    // Broadcast to all clients to update UI
    io.emit("notification_read", notificationId);
  });

  socket.on("disconnect", () => {
    console.log("Client disconnected");
  });
});

const PORT = 3001;
server.listen(PORT, () => {
  console.log(`Notification server running on port ${PORT}`);
});
