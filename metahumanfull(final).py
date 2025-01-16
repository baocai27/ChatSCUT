# -*- coding: utf-8 -*-
import hashlib
import hmac
import json
import sys
import time
from datetime import datetime
import base64
import requests
import os
import audio2face_pb2
import audio2face_pb2_grpc
import grpc
import numpy as np
import soundfile
from flask import Flask, request,jsonify
from flask_cors import CORS
import re
app = Flask(__name__)
CORS(app)
# 这里放函数什么的
if sys.version_info[0] <= 2:
    from httplib import HTTPSConnection
else:
    from http.client import HTTPSConnection

# Tencent Cloud TTS API parameters
secret_id = "AKIDW8iBkNo7EDzriXGpJg0FNKLJA0qZEB99"
secret_key = "EF9wb8lOsHnZFjLvdEkBcuGau5jQ8lKj"
token = ""
service = "tts"
host = "tts.tencentcloudapi.com"
region = "ap-guangzhou"
version = "2019-08-23"
action = "TextToVoice"

# Audio2Face parameters
a2f_url = "localhost:50051"
instance_name = '/World/audio2face/PlayerStreaming'

def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def generate_tts_audio(text, output_audio_path):
    timestamp = int(time.time())
    date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
    
    payload = "{\"Text\":\"" + text.replace('\n', '') + "\",\
        \"SessionId\":\"session-1234\",\
        \"ModelType\":1,\
        \"VoiceType\":301039,\
        \"Codec\":\"wav\",\
        \"EnableSubtitle\":true,\
        \"SampleRate\":24000,\
        \"EmotionCategory\":\"angry\",\
        \"EmotionIntensity\":100}"
    params = json.loads(payload)
    algorithm = "TC3-HMAC-SHA256"

    http_request_method = "POST"
    canonical_uri = "/"
    canonical_querystring = ""
    ct = "application/json; charset=utf-8"
    canonical_headers = "content-type:%s\nhost:%s\nx-tc-action:%s\n" % (ct, host, action.lower())
    signed_headers = "content-type;host;x-tc-action"
    hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    canonical_request = (http_request_method + "\n" +
                         canonical_uri + "\n" +
                         canonical_querystring + "\n" +
                         canonical_headers + "\n" +
                         signed_headers + "\n" +
                         hashed_request_payload)

    credential_scope = date + "/" + service + "/" + "tc3_request"
    hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    string_to_sign = (algorithm + "\n" +
                      str(timestamp) + "\n" +
                      credential_scope + "\n" +
                      hashed_canonical_request)

    secret_date = sign(("TC3" + secret_key).encode("utf-8"), date)
    secret_service = sign(secret_date, service)
    secret_signing = sign(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (algorithm + " " +
                     "Credential=" + secret_id + "/" + credential_scope + ", " +
                     "SignedHeaders=" + signed_headers + ", " +
                     "Signature=" + signature)

    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json; charset=utf-8",
        "Host": host,
        "X-TC-Action": action,
        "X-TC-Timestamp": timestamp,
        "X-TC-Version": version
    }
    if region:
        headers["X-TC-Region"] = region
    if token:
        headers["X-TC-Token"] = token

    try:
        req = HTTPSConnection(host)
        req.request("POST", "/", headers=headers, body=payload.encode("utf-8"))
        resp = req.getresponse()
        result = resp.read().decode('utf-8').split('{')[2].split(':')[1].split(',')[0].strip('"')
        print("TTS generation result received")
    except Exception as err:
        print(err)
        return

    with open(output_audio_path, "wb") as wav_file:
        decode_string = base64.b64decode(result)
        wav_file.write(decode_string)
    print(f"TTS audio saved to {output_audio_path}")


def stream_audio_to_audio2face(audio_path, url, instance_name):
    data, samplerate = soundfile.read(audio_path, dtype="float32")

    if len(data.shape) > 1:
        data = np.average(data, axis=1)

    chunk_size = samplerate // 10
    sleep_between_chunks = 0.001
    block_until_playback_is_finished = True

    with grpc.insecure_channel(url) as channel:
        stub = audio2face_pb2_grpc.Audio2FaceStub(channel)

        def make_generator():
            start_marker = audio2face_pb2.PushAudioRequestStart(
                samplerate=samplerate,
                instance_name=instance_name,
                block_until_playback_is_finished=block_until_playback_is_finished,
            )
            yield audio2face_pb2.PushAudioStreamRequest(start_marker=start_marker)
            for i in range(len(data) // chunk_size + 1):
                time.sleep(sleep_between_chunks)
                chunk = data[i * chunk_size: i * chunk_size + chunk_size]
                yield audio2face_pb2.PushAudioStreamRequest(audio_data=chunk.astype(np.float32).tobytes())

        request_generator = make_generator()
        print("Sending audio data...")
        response = stub.PushAudioStream(request_generator)
        if response.success:
            print("Audio streamed to Audio2Face successfully")
        else:
            print(f"ERROR: {response.message}")
    print("Channel closed")








@app.route("/", methods=['POST'])
def metaHuman():
    if request.is_json:
        text = request.get_json().get("message", "")
        print(text)
        
        # Encode and decode to ignore any non-utf-8 characters
        text = text.encode('utf-8', 'ignore').decode('utf-8', 'ignore')
        
        # Remove extra spaces
        segments = re.split(r'[。；]\s*', text)
        
        
        # Split text by period followed by optional whitespace
        segments = re.split(r'\。\s*', text)
        for segment in segments:
            print("/n")
            print(segment)  
        TEXT_FILE_PATH = 'C:\\Users\\13157\\Desktop\\AISYS\\llmresponse.txt'
        AUDIO_OUTPUT_PATH = 'C:\\Users\\13157\\Desktop\\AISYS\\temp.wav'
        
        for segment in segments:
            if segment:  # Ensure segment is not empty
                with open(TEXT_FILE_PATH, "w", encoding="utf-8") as file:
                    file.write(segment)
                
                with open(TEXT_FILE_PATH, 'r', encoding='utf-8') as file:
                    text1 = file.read()
                
                generate_tts_audio(text1, AUDIO_OUTPUT_PATH)
                stream_audio_to_audio2face(AUDIO_OUTPUT_PATH, a2f_url, instance_name)
        
        return jsonify({'done': 'done'}) 
    else:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    
if __name__ == "__main__":
    app.run('0.0.0.0',port=3050,debug=True)