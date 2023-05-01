import phe as paillier
import json
import Pyro4
from sklearn.metrics import mean_absolute_percentage_error
import pandas as pd
from sklearn.model_selection import train_test_split 


client2 = Pyro4.Proxy("PYRONAME:RMI.LR")
class MakeKeys: #this class helps to make a public and private key pair
	def __init__(self):
		public_key, private_key = paillier.generate_paillier_keypair() #generate public and private key pair
		keys={}
		keys['public_key'] = {'n': public_key.n}
		keys['private_key'] = {'p': private_key.p,'q':private_key.q}
		with open('keys.json', 'w') as file: #store the public and private key in keys.json so that client can use anytime latter
			json.dump(keys, file)

class Client:
	def getKeys(self):
		with open('keys.json', 'r') as file: 
			keys=json.load(file)
			pub_key=paillier.PaillierPublicKey(n=int(keys['public_key']['n'])) #getting the public key
			priv_key=paillier.PaillierPrivateKey(pub_key,keys['private_key']['p'],keys['private_key']['q']) #getting the private key
		return pub_key, priv_key 

	def serializeData1(self,public_key, data):
		encrypted_data_list = [public_key.encrypt(x) for x in data] #encrypting the data first before sending to the client
		encrypted_data={}
		encrypted_data['public_key'] = {'n': public_key.n}
		encrypted_data['values'] = [(str(x.ciphertext()), x.exponent) for x in encrypted_data_list]
		serialized = json.dumps(encrypted_data)
		with open('data.json', 'w') as file: #sending these encrypted data to the server
			json.dump(serialized, file)
		# server
		client2.serializeData(1) #asking server for prediction of our question
	
	def loadAnswer(self):
		with open('answer.json', 'r') as file: #getting the encrypted response from the server
			ans=json.load(file)
		answer=json.loads(ans)
		answer_key=paillier.PaillierPublicKey(n=int(answer['public_key']['n']))
		ans = paillier.EncryptedNumber(answer_key, int(answer['values'][0]), int(answer['values'][1]))
		if (answer_key==public_key): #checking if the public key is correct or not
			return ans
    
	def getActualParameters(self): #this function is used for analysis purpose for finding the accuracy
		w,b = client2.getActualParameters()
		return [w,b]


MakeKeys() #first crate a public and private key pair and store somewhere
client1 = Client()
public_key, private_key = client1.getKeys() #store the keys in the corresponding variables
data =[241,400,601,1000000]
client1.serializeData1(public_key, data) #encrypting the data and sending the data to server and server will give the response


print(f"With Encryption: {private_key.decrypt(client1.loadAnswer())}") #decripting the predictiion that the server will give

w,b = client1.getActualParameters()
print(f"Without encryption : {sum([data[i]*w[i] for i in range(len(w))]) + b}")


############################ Finding the accuracy of the inputs without encryption and with encryption ##############################################
file = open('parameters.json','r')
p = json.load(file)


data_frame=pd.read_excel('Google_Stock_Price.xlsx')
y=data_frame.Close
X=data_frame.drop('Close',axis=1)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=0) #getting the test data

a = list(X_test.to_numpy())

y_prediction = []
# for this analysis all the test datas are encrypted and decrypted using same public key and private key pair
for i in a:
	l = []
	for j in i:
		l.append(int(j))
	client1.serializeData1(public_key,l) #getting the server predction
	y_prediction.append(private_key.decrypt(client1.loadAnswer())) #decrypting the response from the server


y_p = pd.DataFrame(y_prediction)
print(f"Accuracy with encryption : {100-mean_absolute_percentage_error(y_test,y_p)} %")
print(f"Accuracy without encryption: {p['accuracy']} %")
#####################################################################################################################################################