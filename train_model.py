import math

import pandas as pd
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, QuantileTransformer
import pickle

class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(4, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        logits = self.linear_relu_stack(x)
        return logits

if __name__ == '__main__':
    # Load and process the data
    df = pd.read_csv('gameplay_history.csv')

    x_cols = ["bird_y", "bird_vertical_movement", "pipe_y", "pipe_dist"]
    y_col = ["space_pressed"]

    # Resample so that we have a more similar number of examples where we press and don't press space
    # Needed since we have an extreme class imbalance
    # If there are too many examples where we press space, the model will be overeager and constantly crash into pipes
    # If we include all examples, it will likely refuse to "jump" at all
    df_true = df[df.space_pressed == 1]
    df_false = df[df.space_pressed == 0]

    len_true = len(df_true.index)

    sample_true = df_true
    sample_false = df_false.sample(n=math.ceil(len_true*4))

    df = pd.concat([sample_true, sample_false])
    print(f"Number of data points after sampling: {len(df.index)}")
    train_df, test_df = train_test_split(df, test_size=0.2)

    scaler = StandardScaler()

    train_x = train_df[x_cols].values
    train_y = train_df[y_col].values

    test_x = test_df[x_cols].values
    test_y = test_df[y_col].values

    train_x = scaler.fit_transform(train_x)
    test_x = scaler.transform(test_x)

    pickle.dump(scaler, open('scaler.pkl', 'wb'))

    class CustomDataset(Dataset):
        def __init__(self, features, targets):
            self.features = torch.tensor(features, dtype=torch.float32)
            self.targets = torch.tensor(targets, dtype=torch.float32)

        def __len__(self):
            return len(self.features)

        def __getitem__(self, idx):
            return self.features[idx], self.targets[idx]

    train_dataset = CustomDataset(train_x, train_y)
    test_dataset = CustomDataset(test_x, test_y)
    train_dataloader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    test_dataloader = DataLoader(test_dataset, batch_size=64, shuffle=True)

    # Define the model

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )
    print(f"Using {device} device")

    model = NeuralNetwork().to(device)
    print(model)

    # Train

    loss_fn = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.0001)

    def train(dataloader, model, loss_fn, optimizer):
        size = len(dataloader.dataset)
        model.train()
        for batch, (X, y) in enumerate(dataloader):
            X, y = X.to(device), y.to(device)

            # Compute prediction error
            pred = model(X)
            loss = loss_fn(pred, y)

            # Backpropagation
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()

            if batch % 1 == 0:
                loss, current = loss.item(), (batch + 1) * len(X)
                print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")


    def test(dataloader, model, loss_fn):
        num_batches = len(dataloader)
        model.eval()
        test_loss, correct = 0, 0
        with torch.no_grad():
            for X, y in dataloader:
                X, y = X.to(device), y.to(device)
                pred = model(X)
                test_loss += loss_fn(pred, y).item()
                correct += torch.sum(pred.round() == y).item()
        test_loss /= num_batches
        accuracy = correct / len(dataloader.dataset)
        print(f"Test loss: {test_loss:>8f}, Accuracy: {accuracy:>8f}\n")
        return test_loss, accuracy

    epochs = 500
    max_eval_accuracy = 0.0
    acc_decreasing = 0
    for t in range(epochs):
        print(f"Epoch {t+1}\n-------------------------------")
        train(train_dataloader, model, loss_fn, optimizer)
        eval_loss, eval_accuracy = test(test_dataloader, model, loss_fn)
        if eval_accuracy > max_eval_accuracy:
            acc_decreasing = 0
        else:
            acc_decreasing+=1
        if acc_decreasing>25:
            print("Early stopping triggered")
            break
        else:
            max_eval_accuracy = max(eval_accuracy, max_eval_accuracy)

    torch.save(model.state_dict(), "model.pth")