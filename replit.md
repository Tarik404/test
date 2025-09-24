# gehitubib - Biblioteca Digital LGBTQ+

## Overview
This is a static frontend website for a digital LGBTQ+ library. The project displays a catalog of books related to LGBTQ+ themes, history, and culture.

## Project Structure
- `index.html` - Main website file containing the complete application
- `schema.sql` - MySQL database schema for the book catalog (for reference)
- `server.py` - Python HTTP server to serve the static content

## Setup Status
- ✅ Python HTTP server configured on port 5000
- ✅ Workflow configured for development
- ✅ Deployment configuration set for production
- ✅ Website fully functional

## Features
- Book catalog with search and filtering
- Modern responsive design with Tailwind CSS
- Pride-themed visual elements
- Admin panel functionality (embedded in JavaScript)
- Category-based book organization

## Architecture
- **Frontend**: Static HTML with embedded JavaScript and CSS
- **Styling**: Tailwind CSS (CDN)
- **Server**: Python HTTP server for development
- **Database**: Currently uses hardcoded data in JavaScript (schema.sql provided for future database integration)

## Development
The website runs on a Python HTTP server that serves the static HTML file with proper cache control headers to work correctly in the Replit iframe environment.

## Recent Changes
- 2025-09-24: Initial setup in Replit environment
- Configured Python HTTP server with cache control headers
- Set up workflow and deployment configuration