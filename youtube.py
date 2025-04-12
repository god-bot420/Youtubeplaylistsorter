import os
import pickle
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from PIL import Image, ImageTk
from io import BytesIO
import requests
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

class YouTubePlaylistOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Playlist Organizer")
        self.root.geometry("1400x800")
        
        # YouTube API setup
        self.youtube = None
        self.client_secrets_file = "client_secret.json"
        self.api_scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
        
        # Current selected video and playlist
        self.current_video = None
        self.selected_playlist = None
        self.selected_videos = []  # Now holds multiple videos
        
        # UI elements
        self.setup_ui()
        
        # Connect to YouTube API
        self.connect_to_youtube_api()
        
        # Load data
        self.load_data()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Playlists
        playlist_frame = ttk.LabelFrame(main_frame, text="Your Playlists")
        playlist_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Playlist listbox with scrollbar
        playlist_scroll = ttk.Scrollbar(playlist_frame)
        playlist_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.playlist_listbox = tk.Listbox(playlist_frame, selectmode=tk.SINGLE, 
                                           font=("Arial", 11), 
                                           yscrollcommand=playlist_scroll.set,
                                           exportselection=0)
        self.playlist_listbox.pack(fill=tk.BOTH, expand=True)
        playlist_scroll.config(command=self.playlist_listbox.yview)
        
        # Bind selection event for playlists
        self.playlist_listbox.bind('<<ListboxSelect>>', self.on_playlist_select)
        
        # Middle panel - Liked Videos
        liked_frame = ttk.LabelFrame(main_frame, text="Your Liked Videos")
        liked_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Liked videos listbox with scrollbar - Now using MULTIPLE selection mode
        liked_scroll = ttk.Scrollbar(liked_frame)
        liked_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.liked_listbox = tk.Listbox(liked_frame, selectmode=tk.MULTIPLE, 
                                        font=("Arial", 11), 
                                        yscrollcommand=liked_scroll.set,
                                        exportselection=0)
        self.liked_listbox.pack(fill=tk.BOTH, expand=True)
        liked_scroll.config(command=self.liked_listbox.yview)
        
        # Bind selection event for videos
        self.liked_listbox.bind('<<ListboxSelect>>', self.on_video_select)
        
        # Right panel - Video Preview
        preview_frame = ttk.LabelFrame(main_frame, text="Video Preview")
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Video thumbnail
        self.thumbnail_label = ttk.Label(preview_frame)
        self.thumbnail_label.pack(pady=10)
        
        # Video title
        self.title_label = ttk.Label(preview_frame, font=("Arial", 12, "bold"), wraplength=350)
        self.title_label.pack(pady=5, padx=10)
        
        # Video description
        description_frame = ttk.Frame(preview_frame)
        description_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        description_scroll = ttk.Scrollbar(description_frame)
        description_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.description_text = tk.Text(description_frame, font=("Arial", 10), 
                                        yscrollcommand=description_scroll.set, 
                                        wrap=tk.WORD, height=10)
        self.description_text.pack(fill=tk.BOTH, expand=True)
        description_scroll.config(command=self.description_text.yview)
        self.description_text.config(state=tk.DISABLED)
        
        # Open in browser button
        self.open_button = ttk.Button(preview_frame, text="Watch on YouTube", 
                                     command=self.open_in_browser)
        self.open_button.pack(pady=10)
        self.open_button.config(state=tk.DISABLED)
        
        # Bottom controls
        controls_frame = ttk.Frame(self.root)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.move_button = ttk.Button(controls_frame, text="Move Selected Videos to Playlist", 
                                     command=self.move_to_playlist)
        self.move_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Refresh Data", 
                  command=self.load_data).pack(side=tk.LEFT, padx=5)
        
        # Selection status labels
        selection_frame = ttk.Frame(controls_frame)
        selection_frame.pack(side=tk.RIGHT, padx=10)
        
        ttk.Label(selection_frame, text="Selected Playlist:").pack(side=tk.LEFT)
        self.playlist_status = ttk.Label(selection_frame, text="None", font=("Arial", 10, "italic"))
        self.playlist_status.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(selection_frame, text="Selected Videos:").pack(side=tk.LEFT, padx=(10, 0))  # Changed to plural
        self.video_status = ttk.Label(selection_frame, text="0 selected", font=("Arial", 10, "italic"))  # Changed default text
        self.video_status.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def connect_to_youtube_api(self):
        credentials = None
        
        # Check if token file exists
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                credentials = pickle.load(token)
                
        # If no credentials or they're invalid, get new ones
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.client_secrets_file, self.api_scopes)
                    credentials = flow.run_local_server(port=0)
                except FileNotFoundError:
                    messagebox.showerror("Error", 
                                        "client_secret.json file not found. Please download it from Google Cloud Console.")
                    return
                
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(credentials, token)
                
        # Build YouTube API client
        self.youtube = build('youtube', 'v3', credentials=credentials)
        self.status_var.set("Connected to YouTube API")
        
    def load_data(self):
        if not self.youtube:
            messagebox.showerror("Error", "Not connected to YouTube API")
            return
            
        self.status_var.set("Loading data from YouTube...")
        self.root.update()
        
        # Clear listboxes
        self.playlist_listbox.delete(0, tk.END)
        self.liked_listbox.delete(0, tk.END)
        
        # Load playlists
        try:
            playlists_response = self.youtube.playlists().list(
                part="snippet",
                mine=True,
                maxResults=50
            ).execute()
            
            self.playlists = []
            for item in playlists_response.get("items", []):
                playlist_id = item["id"]
                title = item["snippet"]["title"]
                self.playlists.append({"id": playlist_id, "title": title})
                self.playlist_listbox.insert(tk.END, title)
                
            # Load all liked videos using pagination
            self.status_var.set("Loading liked videos (this may take a moment)...")
            self.root.update()
            
            self.liked_videos = []
            next_page_token = None
            
            while True:
                request_args = {
                    "part": "snippet,contentDetails",
                    "myRating": "like",
                    "maxResults": 50  # Maximum allowed by the API
                }
                
                if next_page_token:
                    request_args["pageToken"] = next_page_token
                    
                liked_response = self.youtube.videos().list(**request_args).execute()
                
                for item in liked_response.get("items", []):
                    video_id = item["id"]
                    title = item["snippet"]["title"]
                    thumbnail_url = item["snippet"]["thumbnails"]["medium"]["url"] if "medium" in item["snippet"]["thumbnails"] else item["snippet"]["thumbnails"]["default"]["url"]
                    description = item["snippet"]["description"]
                    self.liked_videos.append({
                        "id": video_id, 
                        "title": title,
                        "thumbnail_url": thumbnail_url,
                        "description": description
                    })
                    self.liked_listbox.insert(tk.END, title)
                
                # Check if there are more pages
                next_page_token = liked_response.get("nextPageToken")
                if not next_page_token:
                    break
                    
                self.status_var.set(f"Loading liked videos... ({len(self.liked_videos)} loaded so far)")
                self.root.update()
                
            self.status_var.set(f"Loaded {len(self.playlists)} playlists and {len(self.liked_videos)} liked videos")
            
            # Select and show first video if available
            if self.liked_videos:
                self.liked_listbox.selection_set(0)
                self.on_video_select(None)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            self.status_var.set("Error loading data")
    
    def on_video_select(self, event):
        selected_indices = self.liked_listbox.curselection()
        if not selected_indices:
            self.selected_videos = []  # Clear selection
            self.video_status.config(text="0 selected")
            return
            
        # Update the list of selected videos
        self.selected_videos = []
        for index in selected_indices:
            self.selected_videos.append(self.liked_videos[index])
        
        # Update video status display
        self.video_status.config(text=f"{len(self.selected_videos)} selected")
        
        # For the preview, show the last selected video
        last_index = selected_indices[-1]
        self.current_video = self.liked_videos[last_index]
        
        # Update preview
        self.update_preview(self.current_video)
        
    def on_playlist_select(self, event):
        selected_indices = self.playlist_listbox.curselection()
        if not selected_indices:
            return
            
        index = selected_indices[0]
        self.selected_playlist = self.playlists[index]
        
        # Update playlist status display
        self.playlist_status.config(text=self.selected_playlist["title"])
        
    def update_preview(self, video):
        # Update title
        self.title_label.config(text=video["title"])
        
        # Update description
        self.description_text.config(state=tk.NORMAL)
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(tk.END, video["description"])
        self.description_text.config(state=tk.DISABLED)
        
        # Load thumbnail
        try:
            response = requests.get(video["thumbnail_url"])
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            photo = ImageTk.PhotoImage(img)
            
            self.thumbnail_label.config(image=photo)
            self.thumbnail_label.image = photo  # Keep a reference
        except Exception as e:
            self.thumbnail_label.config(image='')
            print(f"Error loading thumbnail: {str(e)}")
        
        # Enable open button
        self.open_button.config(state=tk.NORMAL)
        
    def open_in_browser(self):
        if not self.current_video:
            return
            
        video_url = f"https://www.youtube.com/watch?v={self.current_video['id']}"
        webbrowser.open(video_url)
    
    def move_to_playlist(self):
        # Check if both playlist and at least one video are selected
        if not self.selected_playlist:
            messagebox.showinfo("Info", "Please select a playlist")
            return
            
        if not self.selected_videos:
            messagebox.showinfo("Info", "Please select at least one video")
            return
            
        try:
            moved_count = 0
            error_count = 0
            
            # Get all the indices in the beginning as they will change when we start removing videos
            video_indices = []
            for selected_video in self.selected_videos:
                for i, video in enumerate(self.liked_videos):
                    if video["id"] == selected_video["id"]:
                        video_indices.append(i)
                        break
            
            # Sort indices in reverse order to ensure we delete from the end first
            video_indices.sort(reverse=True)
            
            for selected_video in self.selected_videos:
                try:
                    # Add to selected playlist
                    self.youtube.playlistItems().insert(
                        part="snippet",
                        body={
                            "snippet": {
                                "playlistId": self.selected_playlist["id"],
                                "resourceId": {
                                    "kind": "youtube#video",
                                    "videoId": selected_video["id"]
                                }
                            }
                        }
                    ).execute()
                    
                    # Remove like from the video
                    self.youtube.videos().rate(
                        id=selected_video["id"],
                        rating="none"
                    ).execute()
                    
                    moved_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Error processing video {selected_video['title']}: {str(e)}")
            
            # Remove videos from liked_videos list and listbox
            # We delete in reverse order to maintain correct indices
            for index in video_indices:
                self.liked_videos.pop(index)
                self.liked_listbox.delete(index)
            
            # Clear the current selection
            self.liked_listbox.selection_clear(0, tk.END)
            self.selected_videos = []
            self.video_status.config(text="0 selected")
            
            # Clear preview if needed
            if self.current_video and any(vid["id"] == self.current_video["id"] for vid in self.selected_videos):
                self.thumbnail_label.config(image='')
                self.title_label.config(text="")
                self.description_text.config(state=tk.NORMAL)
                self.description_text.delete(1.0, tk.END)
                self.description_text.config(state=tk.DISABLED)
                self.open_button.config(state=tk.DISABLED)
                self.current_video = None
            
            message = f"Moved {moved_count} videos to playlist '{self.selected_playlist['title']}'"
            if error_count > 0:
                message += f" ({error_count} errors)"
            
            messagebox.showinfo("Success", message)
            self.status_var.set(message)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to move videos: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubePlaylistOrganizer(root)
    root.mainloop()