import cgi
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
from os import curdir, sep
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

from train_lego import *


# Verkrijgt de JSON credentials die gebruikt worden om in te loggen op firebase
cred = credentials.Certificate('robocamera.json')

# initialiseerd firebase admin
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://robocamera-322ea.firebaseio.com/'
})
#zet de reference op "tabel" recognized. Tabel tussen aanhalingstekens want firebase is NOSQL
DB_recognized = db.reference("recognized")

#leegt de database aan het begin ff
DB_recognized.set("")

#de volgende klasses worden onderzocht
classes = ['blauw_2x2', 'blauw_4x2','groen_2x2','groen_4x2','rood_2x2','rood_4x2']
trainPaths = ['./data/' + c + '/train/' for c in classes]
testPaths = ['./data/' + c + '/test/' for c in classes]

#de klassen waarmee de camera wordt getrained.
trainer = Trainlego(classes, trainPaths)
cam = Camera(0)

nteller =0
className = "niks nada noppes nog niets...."

tree = None
cameraQuality = 30


class httpServerRoboCamera(BaseHTTPRequestHandler):
    """
        do_GET is een functie van baseHTTPRequesthandler of althans dat de naam van de functie die je overwrite dit is wanneer er
            een get request wordt gestuurd naar de server
        do_POST dit is de functie die code afhandeld wanneer er een POST request wordt verstuurd naar de server.
            In ons geval heeft dit meer met de quality van de camera te maken. Hoe hoger deze is des te meer vertraging erin zit maar als die te laag staat zie je niks.
    """
    def do_GET(self):
        global cameraQuality
        global nteller
        global tree
        global className
        global cam
        try:
            self.path=re.sub('[^.a-zA-Z0-9]', "",str(self.path))
            if self.path=="" or self.path==None or self.path[:1]==".":
                return
            if self.path.endswith(".html"):
                #laad de HTML pagina in index.html
                f = open(curdir + sep + self.path)
                self.send_response(200)
                self.send_header('Content-type',	'text/html')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
            if self.path.endswith(".mjpeg"):
                #laad de camera in
                self.send_response(200)
                self.wfile.write("Content-Type: multipart/x-mixed-replace; boundary=--aaboundary")
                self.wfile.write("\r\n\r\n")
                while 1:
                    #constante flow van de camera zolang het script draait vandaar de while 1

                    #verkrijg camera image
                    img = cam.getImage()

                    #voorkom dat de cam te snel update
                    if nteller > 4:

                        #classify wat je ziet
                        className = tree.classify(img)
                        # f = open('currentClass.txt', 'w')
                        # f.write(classN ame)
                        # f.close()

                        #push het naar de realtime firebase database.
                        DB_recognized.push({
                            'type': className,
                            'time': str(time.time())
                        })
                        nteller = 0
                    else:
                        nteller += 1

                    #update de livestream met wat je ziet in het rood
                    img.drawText(className, 10, 10, fontsize=60, color=Color.RED)
                    img = img.applyLayers()

                    #convert en voeg de juiste headers toe
                    cv2mat=cv.EncodeImage(".jpeg",img.getBitmap(),(cv.CV_IMWRITE_JPEG_QUALITY,cameraQuality))
                    JpegData=cv2mat.tostring()
                    self.wfile.write("--aaboundary\r\n")
                    self.wfile.write("Content-Type: image/jpeg\r\n")
                    self.wfile.write("Content-length: "+str(len(JpegData))+"\r\n\r\n" )
                    self.wfile.write(JpegData)
                    self.wfile.write("\r\n\r\n\r\n")
                    time.sleep(0.05)
                return
            if self.path.endswith(".jpeg"):

                #zoekt de jpeg file die die moet zoeken
                f = open(curdir + sep + self.path)
                self.send_response(200)
                self.send_header('Content-type','image/jpeg')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
            return
        except IOError:
            #gooi 404
            self.send_error(404,'File Not Found: %s' % self.path)
    def do_POST(self):
        global rootnode, cameraQuality
        try:
            #update camera
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                query=cgi.parse_multipart(self.rfile, pdict)
            self.send_response(301)

            self.end_headers()
            upfilecontent = query.get('upfile')
            print "filecontent", upfilecontent[0]
            value=int(upfilecontent[0])
            cameraQuality=max(2, min(99, value))
            self.wfile.write("<HTML>POST OK. Camera Set to<BR><BR>");
            self.wfile.write(str(cameraQuality));

        except :
            pass

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
#class ThreadedHTTPServer(HTTPServer):
    """Handle requests in a separate thread."""

def main():
    global tree

    #train de classifiers met traindata
    trainer.trainen()
    tree = trainer.classifiers[1]
    #test random afbeelding
    imgs = ImageSet()
    for p in testPaths:
        imgs += ImageSet(p)
    random.shuffle(imgs)
    #ff tussendoor updateje
    print "Result padum padum spannond..."
    trainer.testen(testPaths)

    #try catch die de server opstart onder localhost:12345
    try:
        server = ThreadedHTTPServer(('localhost', 12345), httpServerRoboCamera)
        print 'started httpserver...'
        print 'dit ff runnen in die git bash om het naar buiten te zetton'
        print 'ssh -R robostream:80:localhost:12345 serveo.net'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

main()

