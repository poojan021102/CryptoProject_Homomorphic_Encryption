import pandas as pd
import phe as paillier
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split 
from sklearn.metrics import mean_absolute_percentage_error
import json
import Pyro4 

class LinearModel:
	def __init__(self):
		self.getResults()

	def getResults(self):
		data_frame=pd.read_excel('Google_Stock_Price.xlsx') #reading the CSV file
		y=data_frame.Close #getting the result column
		X=data_frame.drop('Close',axis=1) #getting all the feature variables
		X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.01, random_state=0) #splitting the variables into training and testing data sets
		model = LinearRegression().fit(X_train, y_train) #creating the model
		y_prediction=model.predict(X_test) #testing the model with the testing dataset
		accuracy=mean_absolute_percentage_error(y_test, y_prediction) #getting accuracy of the model using test dataset
		return model, 100-accuracy

	def getCoef(self): #getting the weights of all the feature variables w and b of the linear regression
		self.t = self.getResults()
		return [self.t[0].coef_,self.t[0].intercept_,self.t[1]]

# class ServerWorker:
# 	def getData(self):
# 		with open('data.json', 'r') as file: 
# 			d=json.load(file)
# 		data=json.loads(d)
# 		return data
	
# 	def predict(self,pubkey,inp):
# 		file = open('parameters.json','r')
# 		d = json.load(file)
# 		file.close()
# 		weight = d["w"]
# 		b = d["b"]
# 		pubkey= paillier.PaillierPublicKey(n=int(pubkey['n']))
# 		enc_nums_rec = [paillier.EncryptedNumber(pubkey, int(x[0], int(x[1]))) for x in inp]
# 		results=sum([enc_nums_rec[i]*weight[i] for i in range(len(enc_nums_rec))]) + b
# 		return results, pubkey

@Pyro4.expose #exposing the server to other client in the form of class object, everytime client arrives then it can use the services offered by the server
class Server(object):
	def getData(self): #get the data which is given by the client
		with open('data.json', 'r') as file: 
			d=json.load(file) #get the json data
		data=json.loads(d) 
		print("Data received from client: \n")
		print(data)
		return data
	
	def predict(self,pubkey,inp): #predict the input encrypted feature values using public key provided by the client
		# note: the server had not generated public key by its own the server is using public key which is strictly provided by the client
		file = open('parameters.json','r') #get the w and b parameters which is there in the model developed above in LinearModel class
		d = json.load(file)
		file.close()
		weight = d["w"] #get all w's of the model
		b = d["b"] #get the intercept of the model
		pubkey= paillier.PaillierPublicKey(n=int(pubkey['n'])) #getting the public key
		encrypted_numbers_received = [paillier.EncryptedNumber(pubkey, int(x[0], int(x[1]))) for x in inp] #encrypting the client's data using public key provided
		results=sum([encrypted_numbers_received[i]*weight[i] for i in range(len(encrypted_numbers_received))]) + b #predict the result of the encrypted data using the model created previously
		return results, pubkey
	def serializeData(self,a): #a is of no use it is used by the client to call this method
		# s = ServerWorker()
		s = self
		data = s.getData()
		results, pubkey = s.predict(data['public_key'],data['values'])
		encrypted_data={}
		encrypted_data['public_key'] = {'n': pubkey.n}
		encrypted_data['values'] = (str(results.ciphertext()), results.exponent) #getting encryted data values from the client
		# print(encrypted_data)
		serialized = json.dumps(encrypted_data) #serialize into a json formate
		with open('answer.json', 'w') as file:
			json.dump(serialized, file) #create a json file and dump these data into answer.json in order to read by client
		return 1 #this is only for client's purpose
	def getActualParameters(self): #this function is used to find the accuracy for calculation between encrypted and unencrypted data
		file = open('parameters.json','r')
		p = json.load(file)
		return [p['w'],p['b']]

cof=LinearModel().getCoef()
j = {
	"w":[(x) for x in cof[0].tolist()],
	"b":(cof[1]),
	"accuracy":(cof[2])
}
with open('parameters.json','w') as file: #store the parameters so that client can also use it to calculate accuracy
	json.dump(j,file)
daemon = Pyro4.Daemon()
ns = Pyro4.locateNS()
uri = daemon.register(Server) #register the server so that the client can locate thourgh its name
ns.register("RMI.LR",uri)
print("Server started")
daemon.requestLoop()
