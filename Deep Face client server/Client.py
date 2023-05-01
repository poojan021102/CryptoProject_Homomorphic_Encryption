import tenseal as ts
from deepface import DeepFace as DF
import base64
import Pyro4
import json
from deepface.commons import distance as dst

client2 = Pyro4.Proxy("PYRONAME:RMI.DeepFace")
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


def make_keys(): #this function makes public and private key and save it to the file for further use
    contextName = ts.context(ts.SCHEME_TYPE.CKKS, poly_modulus_degree = 8192, coeff_mod_bit_sizes = [60, 40, 40, 60])
    contextName.generate_galois_keys()
    contextName.global_scale = 2**40
    secretContext = contextName.serialize(save_secret_key = True)
    WriteDataToFile("private_key.txt", secretContext)
 
    contextName.make_context_public() 
    publicContext = contextName.serialize() #serialize the context inorder to save
    WriteDataToFile("public_key.txt", publicContext)
    keys={}
    keys['public_key'] = "public_key.txt"
    keys['private_key'] = "private_key.txt"
    with open('keys.json', 'w') as file: 
        json.dump(keys, file)


class Client:
    def predict(self,img_path1,img_path2):
        self.img1_embedding = DF.represent(img_path=img_path1,model_name="Facenet")[0]['embedding'] #get embedding of first image
        self.img2_embedding = DF.represent(img_path=img_path2,model_name="Facenet")[0]['embedding'] #get embedding of second image
        with open('keys.json', 'r') as file: 
            keys=json.load(file)
        context = ts.context_from(ReadDataFromFile(keys["private_key"]))
 
        encrypted_1 = ts.ckks_vector(context, self.img1_embedding) #encrypt first image
        encrypted_2 = ts.ckks_vector(context, self.img2_embedding) #encrypt second image
        
        encrypted_1_photo = encrypted_1.serialize() #serialize first enrypted image inorder to save
        encrypted_2_photo = encrypted_2.serialize() #serialze second encrypted image inorder to save
        
        WriteDataToFile("encryptedPic1.txt", encrypted_1_photo)
        WriteDataToFile("encryptedPic2.txt", encrypted_2_photo) #write to the file
        data={}
        data['public_key'] = keys["public_key"]
        data["embedding_1"] = "encryptedPic1.txt"
        data["embedding_2"] = "encryptedPic2.txt"
        with open('data.json', 'w') as file:
            json.dump(data, file)
        client2.check_same() #call the server and find the Euclidean Squared distance between encyrpted images
        context = ts.context_from(ReadDataFromFile(keys["private_key"])) #get the keys
 
        #load euclidean squared value
        with open('euclidean_squared.json', 'r') as file: 
            d=json.load(file)
        euclidean_squared_photo = ReadDataFromFile(d["euclidean_squared"]) #get the Euclidean squared distance 
        euclidean_squared = ts.lazy_ckks_vector_from(euclidean_squared_photo) 
        euclidean_squared.link_context(context)
        
        #decrypt it
        euclidean_squared_plain = euclidean_squared.decrypt()[0] #decrypt the Euclidean squred using private key
        if euclidean_squared_plain < 100:
            print("they are same person")
        else:
            print("they are different persons")
        return euclidean_squared_plain
    def getActual(self):
        dist = dst.findEuclideanDistance(self.img1_embedding, self.img2_embedding) #find Euclidean Squared distance without any Encryption
        return dist * dist
make_keys() #genereate public and private key pairs
c = Client()
a = c.predict("two1.png","one1.png")
print(f"With encryption the euclidean squared distance : {a}")
print(f"Without encryption the euclidean squared distance: {c.getActual()}") #get the distance without encryption for analysis purpose