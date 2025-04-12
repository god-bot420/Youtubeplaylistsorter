# YouTube Playlist Organizer

The **YouTube Playlist Organizer** is a Python-based desktop application that allows users to manage their YouTube playlists and liked videos. It provides an intuitive graphical interface for organizing videos, moving them between playlists, and previewing video details.

## Features

- **YouTube API Integration**: Connects to your YouTube account to access playlists and liked videos.
- **Playlist Management**: View and select your playlists.
- **Liked Videos Management**: View and select multiple liked videos.
- **Move Videos**: Move selected liked videos to a chosen playlist.
- **Video Preview**: Displays video thumbnails, titles, and descriptions.
- **Open in Browser**: Watch videos directly on YouTube with a single click.
- **Refresh Data**: Reload playlists and liked videos at any time.

## Prerequisites

Before running the application, ensure you have the following:

1. **Python 3.7 or higher** installed on your system.
2. **Google API Credentials**:
   - Create a project in the [Google Cloud Console](https://console.cloud.google.com/).
   - Enable the **YouTube Data API v3** for your project.
   - Download the `client_secret.json` file and place it in the project directory.

3. Install the required Python packages:
   ```bash
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib pillow requests
