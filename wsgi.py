from app import create_app

app = create_app()

# This file acts as the official entry point for Vercel's serverless functions.
# Vercel looks for the 'app' variable in recognized filenames like wsgi.py or app.py
if __name__ == '__main__':
    app.run()
