from train_model import NeuralNetwork
import torch
import pickle
import numpy as np
from sklearn.preprocessing import StandardScaler

device = (
    "cuda"
    if torch.cuda.is_available()
    else "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)

model = NeuralNetwork().to(device)
model.load_state_dict(torch.load("model.pth", weights_only=True))
scaler = pickle.load(open("scaler.pkl", "rb"))
def predict(control_data):
    control_data = np.array(control_data)
    control_data = control_data.reshape(1, -1)
    control_data = scaler.transform(control_data)
    print(control_data)
    control_tensor = torch.tensor(control_data, dtype=torch.float32).to(device)
    with torch.no_grad():
        prediction = model(control_tensor)
        prediction = prediction[0].detach().numpy()
        print(prediction)
        return prediction