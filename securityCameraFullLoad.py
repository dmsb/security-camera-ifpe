from flask import Flask, render_template, stream_with_context
import cv2
import logging
import subprocess
import re

#instatiate flask app  
app = Flask(__name__, template_folder='./templates')

#metodo para resgatar os ips das cameras de seguranca. (deve-se ser consultado do banco)
addresses = subprocess.check_output(['arp', '-a'])

networkAdds = addresses.decode('windows-1252').splitlines()

#variavel temporaria pra testar multiplas cameras
cameraIPsToConnect = [0]

for networkMapItem in networkAdds :
    if len(networkMapItem) > 0 and networkMapItem.split()[1] == '60-23-a4-b4-1b-8f':
        cameraIPsToConnect.append(networkMapItem.split()[0])
#metodo para resgatar os ips das cameras de seguranca. (deve-se ser consultado do banco)

print(cameraIPsToConnect)

videoCaptures = []
for cameraToConnect in cameraIPsToConnect:
    ipRegexCheckResult = re.search("^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$", str(cameraToConnect))
    print(ipRegexCheckResult)
    if ipRegexCheckResult:
        rtspConnetion = 'rtsp://admin:NUHIDF@'+cameraToConnect+':554/H.264'
    else:
        rtspConnetion = cameraToConnect
    print(rtspConnetion)
    videoCaptures.append(cv2.VideoCapture(rtspConnetion))

#camera = cv2.VideoCapture('rtsp://admin:NUHIDF@192.168.15.8:554/H.264')
#camera = cv2.VideoCapture(0)
def gen_frames(index):  # generate frame by frame from camera

    while True:
        success, frame = videoCaptures[index].read()
        if success:
            try:
                #ret, buffer = cv2.imencode('.jpg', cv2.flip(frame,1))
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                logging.exception(e)
                print(e)
                pass
        else:
            pass

@app.route('/')
def index():
    return render_template('indexFullLoad.html', len = len(cameraIPsToConnect))

@app.route('/video_feed/<int:index>')
def video_feed(index):
    return app.response_class(stream_with_context(gen_frames(index)), mimetype='multipart/x-mixed-replace; boundary=frame')
    #return Response(gen_frames(index), mimetype='multipart/x-mixed-replace; boundary=frame')
        
if __name__ == '__main__':
    app.run(debug=True)







def processCamera():
    # Create an object to read
    # from camera
    video = cv2.VideoCapture('rtsp://admin:NUHIDF@192.168.15.9:554/H.264')

    # We need to check if camera
    # is opened previously or not
    if not video.isOpened():
        print("Error reading video file")

    # We need to set resolutions.
    # so, convert them from float to integer.
    frame_width = int(video.get(3))
    frame_height = int(video.get(4))

    size = (frame_width, frame_height)

    # Below VideoWriter object will create
    # a frame of above defined The output
    # is stored in 'output.avi' file.
    result = cv2.VideoWriter('output.avi',
                            cv2.VideoWriter_fourcc(*'MJPG'),
                            10, size)

    while True:
        ret, frame = video.read()

        if ret:

            # Write the frame into the
            # file 'output.avi'
            result.write(frame)

            # Display the frame
            # saved in the file
            cv2.imshow('Frame', frame)

            # Press q on keyboard
            # to stop the process
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Break the loop
        else:
            break

    # When everything done, release
    # the video capture and video
    # write objects
    video.release()
    result.release()

    # Closes all the frames
    cv2.destroyAllWindows()

    print("The video was successfully saved")
