module.exports = {
    apps: [{
        name: "giftschart-bot",
        script: "telegram_bot.py",
        cwd: "/root/01studio/giftschart",
        interpreter: "python3",
        autorestart: true,
        watch: false,
        max_memory_restart: "1G",
        env: {
            NODE_ENV: "production",
            PYTHONUNBUFFERED: "1"
        }
    }, {
        name: "gift-generator-cron",
        script: "pregenerate_gift_cards.py",
        cwd: "/root/01studio/giftschart",
        interpreter: "python3",
        autorestart: true,
        watch: false,
        max_memory_restart: "500M",
        env: {
            PYTHONUNBUFFERED: "1"
        }
    }, {
        name: "giftschart-cdn",
        script: "cdn_server.py",
        cwd: "/root/01studio/giftschart",
        interpreter: "python3",
        autorestart: true,
        watch: false,
        max_memory_restart: "300M",
        env: {
            PYTHONUNBUFFERED: "1"
        }
    }]
};
