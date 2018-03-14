from flask import Flask, request, jsonify, abort
import json, urllib
import world2 as world

app = Flask(__name__)

timeZoneUrlBase = 'http://api.timezonedb.com/v2/'
key = open('key.txt','r').read().splitlines()[0] #read key so that I don't put this on the internet

############################################
#               FLASK INTERFACE            #
############################################
@app.route('/')
def hello_world():
    return 'By Ian Faust'

@app.route("/timeZoneLookup", methods=['GET'])
def query():

    try:
        lat = float(request.args.get('latitude'))
        lng = float(request.args.get('longitude'))
        bear = float(request.args.get('bearingInDegrees'))
        dist = float(request.args.get('distanceInMeters'))
    except TypeError:
        throwErrorCode(True, 400, 'Missing or misformatted input')
    except ValueError:                       
        throwErrorCode(True, 400, 'Missing or misformatted input') #test if all inputs provided

    throwErrorCode(lat > 90. or lat < -90., 500,'latitude value outside of range')
    throwErrorCode(lng > 180. or lng < -180., 500,'longitude outside of range')
    throwErrorCode(bear > 360. or bear <0., 500,'bearing outside of range')
    throwErrorCode(abs(lat) == 90. and lng != 0., 500, 'there is no longitude at the pole')
    
    #convert data to proper radians
    latinp, lnginp, bearinp = world.convert(lat, lng, bear) #convert to proper values in radians
    
    #solve for new longitude and latitude
    latout, lngout = world.eval(latinp, lnginp, bearinp, dist)

    try:    
        output = getTimeZone(latout,lngout)
    except IndexError:
        throwErrorCode(True, 501, 'TimeZoneDB API failure')
        output = None
        
    return output
        
############################################
#             ERROR HANDLING               #
############################################

def throwErrorCode(logic, code, string):
    if logic:
        abort(code, string)
        
############################################
#            TIMEZONEDB API INTERFACE      #
############################################

def getTimeZone(latitude, longitude):
    # This function interfaces with the timezone API (DOES NOT WORK IN PYTHON 3)

    print(latitude,longitude)
    #encode query url string
    timeZoneAPIQuery =urllib.urlencode({"key":key,
                                        "by":'position',
                                        "format":'json',
                                        "lat":str(latitude),
                                        "lng":str(longitude)})

    #query the API through the urlopen function
    print(timeZoneUrlBase+'get-time-zone?'+timeZoneAPIQuery)
    response = urllib.urlopen(timeZoneUrlBase+'get-time-zone?'+timeZoneAPIQuery)
    data = json.loads(response.read()) #convert json response to a dict
    
    #generate a json to post online
    return jsonify(currentLocalTime=data['formatted'].split()[-1], #fomatted as Y-m-d h:i:s, I just want the latter half
                   timeZoneName=data['zoneName'])
