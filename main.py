from urllib.request import urlopen
from bs4 import BeautifulSoup
import ssl
from gtts import gTTS
from pydub import AudioSegment
import re
import random
import yt_dlp
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip
from PIL import Image, ImageDraw, ImageFont
import os
from moviepy.config import change_settings
import textwrap

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Inputs for Reddit and YouTube
url_c_yt = input('Enter yt search name - ')
url_i = input('Enter community name- ')
input_choice = input('Choose between Hot/New/Top/Rising: ')
url = 'https://www.reddit.com/r/' + url_i + '/' + input_choice.lower() + '/'
html = urlopen(url, context=ctx).read()
soup = BeautifulSoup(html, "html.parser")
list_1 = []

# Retrieve all of the anchor tags
for link in soup.find_all('a', href=True):
    href = link['href']
    if "comments" in href:
        if href.startswith("https://www.reddit.com"):
            href = href.replace("https://www.reddit.com", "")
        if href not in list_1:
            list_1.append(href)
            print(href)

# User selects a Reddit post
choice = int(input('Choose number: '))
url_2 = 'https://www.reddit.com' + list_1[choice]
html_2 = urlopen(url_2, context=ctx).read()
soup_2 = BeautifulSoup(html_2, "html.parser")
post_content = soup_2.find_all('div', class_="md")

# Get the post title
post_title = soup_2.find('h1', {'aria-label': True})
if post_title:
    aria_label = post_title['aria-label']

# Extract Reddit post content
content_reddit = ""  # Initialize an empty string

# Append the aria_label as the first sentence
if aria_label:
    content_reddit += aria_label[12:] + "."  # Title as the first sentence with a space after it

# Append the Reddit post content
for content in post_content:
    content_reddit += content.get_text().replace('\n', '')  # Replace new lines with spaces

print(content_reddit)

# Convert Reddit post content to speech using gTTS
tts = gTTS(text=content_reddit, lang='en', tld='co.uk')
tts.save('reddit_post_audio.mp3')

# Speed up the audio using pydub
AudioSegment.ffmpeg = r"C:\ffmpeg\bin\ffmpeg.exe"
AudioSegment.ffprobe = r"C:\ffmpeg\bin\ffprobe.exe"
audio = AudioSegment.from_file('reddit_post_audio.mp3')
audio = audio.speedup(playback_speed=1.40)
audio.export('reddit_post_audio_spedup.mp3', format='mp3')

# Download random YouTube video
url_yt = 'https://www.youtube.com/results?search_query=' + url_c_yt.lower().replace(' ', '+') + '&sp=EgQYAzAB'
html_yt = urlopen(url_yt, context=ctx).read()
soup_yt = BeautifulSoup(html_yt, "html.parser")
video_links = re.findall(r'(/watch\?v=[\w-]+)', str(soup_yt))
video_links = list(set(video_links))
random_video = 'https://www.youtube.com' + video_links[2]  # Pick a random video link

# Download the video using yt-dlp
script_directory = os.path.dirname(os.path.abspath(__file__))
video_file = os.path.join(script_directory, 'downloaded_video.mp4')
if os.path.exists(video_file):
    os.remove(video_file)

ydl_opts = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
    'merge_output_format': 'mp4',
    'outtmpl': video_file
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([random_video])

# Load video and audio
video_clip = VideoFileClip(video_file)
audio_clip = AudioFileClip('reddit_post_audio_spedup.mp3')

# Function to create subtitle clips with text overlay
def create_subtitle_clip(text, start_time, duration, video_size=(1280, 720), font_size=40):
    wrapped_text = textwrap.fill(text, width=40)  # Wrap text to fit on the screen
    subtitle_clip = (TextClip(wrapped_text, fontsize=font_size, color='white', font='Arial-Bold')
                     .set_position(('center', 'center'))
                     .set_duration(duration)
                     .set_start(start_time))
    return subtitle_clip

change_settings({"IMAGEMAGICK_BINARY": "C:/Program Files/ImageMagick-7.1.1-Q16-HDRI/magick.exe"})

# Calculate total characters and T1

total_characters_2 = list(content_reddit)
total_characters = (len(total_characters_2))
audio_duration = audio_clip.duration
T1 = audio_duration / total_characters  # Time per character

# Split Reddit content by sentences
sentences = re.split(r'(?<=\.)\s+', content_reddit.strip())  # Split by sentences,,
text_clips = []
start_time = 0

# Create subtitle clips
for sentence in sentences:
    if sentence.strip():  # Ensure the sentence is not empty
        sentence_duration = len(list(sentence)) * T1  # Calculate duration for the sentence
        text_clips.append(create_subtitle_clip(sentence.strip(), start_time, sentence_duration))
        start_time += sentence_duration  # Update start time for the next sentence

# Trim the video to match the duration of the audio
video_duration = int(audio_clip.duration)
downloaded_video = video_clip.subclip(0, video_duration)

# Combine video, audio, and subtitles
final_video = CompositeVideoClip([downloaded_video] + text_clips).set_audio(audio_clip)

# Save the final video
output_path = 'final_video_with_audio.mp4'
final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')

print("Video with subtitles has been successfully created and saved as 'final_video_with_audio.mp4'")
