from flask import Flask, render_template,request,session
import ibm_boto3
from ibm_botocore.client import Config, ClientError
import requests
import ibm_db
import re
import json
import webbrowser
import os.path
app = Flask(__name__)
slight =["slight_scratch","slight_deformation","car_light_crack","side_mirror_scratch","side_mirror_crack","side_mirror_drop_off"]
moderate =["fender/headlight_damage","fender/bumper_damage","car_light_severe_crack","car_light_damage","windshield_damage"] 
severe=["severe_scratch","medium_deformation","severe_deformation","crack_and_hole"]
app.secret_key = 'a'
con = ibm_db.connect("DATABASE=bludb;HOSTNAME=ba99a9e6-d59e-4883-8fc0-d6a8c9f7a08f.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=31321;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=ykj37771;PWD=d32BgBEhZIAMsbyW;", "", "")
print("connection successful")
@app.route('/')
def home():
    return render_template('index.html')
@app.route('/about')
def home1():
    return render_template('about.html')
@app.route('/login')
def login1():
    return render_template('login.html')
@app.route('/register')
def register1():
    return render_template('register.html')
@app.route('/image')
def img1():
    return render_template('image.html')
@app.route('/result')
def result1():
   return render_template('result.html')

@app.route('/register',methods=['POST'])
def register():
    Username=request.form['Username']
    Email=request.form['Email']
    Password=request.form['Password']
    if not Username:
        error='Username is required and it must not be numeric.'
        return render_template('register.html',error=error)
    if not Email:
        error = 'Email is required.'
        return render_template('register.html',error=error)
    if not Password:
        error= 'Password is required.'
        return render_template('register.html',error=error)
    insert_sql = "INSERT INTO REGISTER VALUES (?,?,?)"
    prepSql=ibm_db.prepare(con,insert_sql)
    ibm_db.bind_param(prepSql, 1, Username)
    ibm_db.bind_param(prepSql, 2, Email)
    ibm_db.bind_param(prepSql, 3, Password)
    result=ibm_db.execute(prepSql)
    return render_template('register.html',msg='Thank you for registering click above to login ')
@app.route('/login',methods=['POST'])
def login():
    Email=request.form['Email']
    Password=request.form['Password']
    if not Email:
        error = 'Email is required.'
        return render_template('login.html',error=error)
    if not Password:
        error= 'Password is required.'
        return render_template('login.html',error=error)
    sql = "SELECT * FROM REGISTER WHERE Email=? AND Password=?"
    smtp = ibm_db.prepare(con,sql)
    ibm_db.bind_param(smtp, 1, Email)
    ibm_db.bind_param(smtp, 2, Password)
    
    ibm_db.execute(smtp)
    account=ibm_db.fetch_assoc(smtp)
    if account:
        return render_template('image.html',msg='Welcome you are successfully logged in')
    else:
        return render_template('register.html',msg='You have entered an invalid username or password or not registerd')

@app.route('/result', methods =['POST'])
def img():
     if request.method=='POST':
          f = request.files['images']
          basepath = os.path.dirname(__file__) #getting the current path i.e where app.py is present
          #print("current path", basepath)
          filepath = os.path.join(basepath, 'uploads', f.filename) #from anywhere in the system we can give image but we want that image later to process so we are saving it to uploads folder for reusing #print("upload folder is", filepath)
          f.save(filepath)
          COS_ENDPOINT = "https://s3.us-south.cloud-object-storage.appdomain.cloud"
          COS_API_KEY_ID = "1PI8G9m1woxT5UIv5dH68iMGunKdutxWKHSv4OIfxc11"
          COS_INSTANCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/07b15bf7929c4d94bae59d59774f0d76:a8fda193-7429-4a80-874f-acf3b0d927d8::"
          cos =ibm_boto3.client("s3", ibm_api_key_id=COS_API_KEY_ID, ibm_service_instance_id=COS_INSTANCE_CRN, config= Config(signature_version="oauth"),endpoint_url=COS_ENDPOINT) 
          cos.upload_file(Filename= filepath, Bucket = 'damageimages',Key='img1.jpg')
          url = "https://vehicle-damage-assessment.p.rapidapi.com/run"
          payload = {"draw_result": True, "remove_background": True,"image": "https://damageimages.s3.us-south.cloud-object-storage.appdomain.cloud/img1.jpg"}
          headers = {"content-type": "application/json", "X-RapidAPI-Key": "080d896cfemsh8f31dd900f9473bp1b1177jsncbe24a43d48b", "X-RapidAPI-Host": "vehicle-damage-assessment.p.rapidapi.com"} 
          response = requests.request("POST",url, json=payload, headers=headers)
          output=response.json()
          print(output)
          webbrowser.open(url)
          cos.upload_file(Filename ="uploads/car.jpg", Bucket='damageimages', Key='img1.jpg')
          a=0
          b=0
          c=0
          l=[]
          for i in range(0,len(output['output']["elements"])):
                 d = output['output']["elements"][i]["damage_category"]
                 l.append(d)
          for i in range(0,len(l)):
              for j in range(0,len(slight)): 
                  if l[i]==slight[j]:
                        a = a+1
          for i in range(0,len(l)):
              for j in range(0,len(moderate)): 
                  if l[i]==moderate[j]:
                        b = b+1
          for i in range(0, len(l)):
              for j in range(0,len(severe)): 
                  if l[i]==severe[j]:
                        c = c+1
          percentage = (a*30 + b*50 +c*80)/(a+b+c)
          damage_parts =set()
          for i in range(0,len(output['output']["elements"])):
                   d = output['output']["elements"][i]["damage_location"]  
                   damage_parts.add(d)
          damage_parts=list(damage_parts)
          if percentage<30:
                result = "Estimated cost is"+ " "+ "20" +"-"+ "30" + "% "+ " " + "of total cost of the parts displayed in the image"
          elif percentage<50:
                result = "Estimated cost is"+ " "+ "30" +"-"+ "50" + "% "+ " " + "of total cost of the parts displayed in the image" 
          else:
                result = "Estimated cost is"+ " "+ "55" +"-"+ "80" + "% "+ " " + "of total cost of the parts displayed in the image"
          print(result)
           
     return render_template('result.html',pred = result)
if __name__ == '__main__':
     app.run(debug=True, host='0.0.0.0')