import Pyro4
import json
import base64
import tenseal as ts

def WriteDataToFile(fileName, txt): #used to write a data to the file
	if type(txt) == bytes:
		#bytes -> base64
		txt = base64.b64encode(txt) #encodeing it so that we can write the data to the file
		 
	with open(fileName, 'wb') as f: 
		f.write(txt)
 
def ReadDataFromFile(fileName): #read the data from a file
	with open(fileName, "rb") as f:
		txt = f.read()
	#base64 -> bytes
	return base64.b64decode(txt) #decode the data that comes to the file so that it become readable

@Pyro4.expose
class Server(object):
	def check_same(self):
		with open('data.json', 'r') as file: 
			data=json.load(file)
		ContextName = ts.context_from(ReadDataFromFile(data["public_key"])) #read the public key given by the client
 
		encrypted_1_photo = ReadDataFromFile(data["embedding_1"]) #read the embedding of first photo given by the client
		encrypted_1 = ts.lazy_ckks_vector_from(encrypted_1_photo) #encrypt the embedding using public key
		encrypted_1.link_context(ContextName)
 
		encrypted_2_photo = ReadDataFromFile(data["embedding_2"]) #read the embedding of second photo given by the client
		encrypted_2 = ts.lazy_ckks_vector_from(encrypted_2_photo) #encrypt the embedding using public key
		encrypted_2.link_context(ContextName)
		
		#euclidean distance
		diff = encrypted_1 - encrypted_2
		euclidSquare = diff.dot(diff) #finding the euclidean_squared distance
		
		#store the HE euclidean_squared distance
		WriteDataToFile("euclidean_squared.txt", euclidSquare.serialize())
		euclidSquare={}
		euclidSquare["euclidean_squared"] = "euclidean_squared.txt"
		with open('euclidean_squared.json', 'w') as file: 
			json.dump(euclidSquare, file)
		return 1

daemon = Pyro4.Daemon()
ns = Pyro4.locateNS()
uri = daemon.register(Server)
ns.register("RMI.DeepFace",uri) #register the server with this name
print("Server started")
daemon.requestLoop()