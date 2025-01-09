import pandas as pd
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split



class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(4, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1),
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

    # Resample so that we have the same number of examples where we press and don't press space
    # Needed since we have an extreme class imbalance

    df_true = df[df.space_pressed == 1]
    df_false = df[df.space_pressed == 0]

    len_true = len(df_true.index)

    sample_true = df_true
    sample_false = df_false.sample(n=len_true)

    df = pd.concat([sample_true, sample_false])
    print(f"Number of data points after sampling: {len(df.index)}")
    train_df, test_df = train_test_split(df, test_size=0.2)

    train_x = train_df[x_cols].values
    train_y = train_df[y_col].values

    test_x = test_df[x_cols].values
    test_y = test_df[y_col].values

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

    loss_fn = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

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

            if batch % 100 == 0:
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
        test_loss /= num_batches
        print(f"Test loss: {test_loss:>8f} \n")
        return test_loss

    epochs = 500
    min_eval_loss = 9999
    loss_increasing = 0
    for t in range(epochs):
        print(f"Epoch {t+1}\n-------------------------------")
        train(train_dataloader, model, loss_fn, optimizer)
        eval_loss = test(test_dataloader, model, loss_fn)
        if eval_loss < min_eval_loss:
            loss_increasing = 0
        else:
            loss_increasing+=1
        if loss_increasing>3:
            print("Early stopping triggered")
            break
        else:
            min_eval_loss = min(eval_loss, min_eval_loss)

    torch.save(model.state_dict(), "model.pth")