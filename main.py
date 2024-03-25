from flask import Flask, render_template, request
from app import summarize, youtube_stats, channel_stats, basic_info, get_answer
import re
import os
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
file_path = ""
cad_name= mail=  no= summary= key_points = ""


def get_video_id(link):
    if "youtu.be" in link:
        return re.search(r"(?<=youtu\.be\/)[^#\?]*", link).group(0)
    else:
        match = re.search(r"(?:[?&]v=|\/embed\/)([^#\?]*)", link)
        return match.group(1) if match else None

@app.route("/")
@app.route("/home", methods=['POST', 'GET'])
def home():
    global cad_name, mail,  no, summary, key_points
    cad_name= mail=  no= summary= key_points = ""
    summary = pro_link = channel_name = likes = views = comment = channel_id = image = sub = videos = ""
    if request.method == 'POST':
        link = request.form.get('link')
        if link:
            pro_link = get_video_id(link)
            summary = summarize(link)
            channel_name, likes, views, comment, channel_id = youtube_stats(pro_link)
            image, sub, videos = channel_stats(channel_id)
    return render_template("home.html", summary=summary, link=pro_link, channel_name=channel_name, likes=likes, views=views, comment=comment, image=image, sub=sub, videos=videos)

@app.route('/chat', methods=['POST', 'GET'])  
def chat():
    global cad_name, mail,  no, summary, key_points
    if request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        filename = file.filename
        global file_path
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        cad_name, mail,  no, summary, key_points = basic_info(file_path)
        return render_template('chat.html', cad_name = cad_name, mail = mail, no = no, summary = summary, key_points= key_points)
    elif request.method == 'GET':
        question = request.args.get('question')
        answer = get_answer(question, file_path)
        return render_template("chat.html", answer=answer, cad_name = cad_name, mail = mail, no = no, summary = summary, key_points= key_points)
        
    

if __name__ == "__main__":
    app.run(debug=True, port=1024)