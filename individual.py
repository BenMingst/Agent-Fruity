import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split

# Set device to GPU if available, otherwise use CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

class AgentModel(nn.Module):
    """
    Defines the PyTorch model for the agent with multiple inputs.
    """
    def __init__(self):
        super(AgentModel, self).__init__()
        
        # Branch 1: Process the 50x50 grid with a convolutional layer
        self.conv_branch = nn.Sequential(
            # Input size: (1, 50, 50)
            nn.Conv2d(in_channels=1, out_channels=32, kernel_size=3, padding=0),
            nn.ReLU(),
            nn.Flatten()
        )
        
        # Branch 2: Process the single integer value
        self.value_branch = nn.Sequential(
            nn.Linear(1, 16),
            nn.ReLU()
        )
        
        # Final layers to produce the output
        self.final_layers = nn.Sequential(
            nn.Linear(self._get_conv_output_size() + 16, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()  # Output layer for 0-1 float
        )
    
    def _get_conv_output_size(self):
        """
        Calculates the output size of the convolutional layers.
        """
        with torch.no_grad():
            dummy_input = torch.randn(1, 1, 50, 50).to(device)
            size = self.conv_branch(dummy_input).size(1)
        return size

    def forward(self, grid_input, value_input):
        """
        Defines the forward pass of the model, combining the two branches.
        """
        # Process each branch
        grid_features = self.conv_branch(grid_input)
        value_features = self.value_branch(value_input)
        
        # Merge the two branches
        merged = torch.cat((grid_features, value_features), dim=1)
        
        # Pass through the final layers
        output = self.final_layers(merged)
        
        return output

def generate_dummy_data(num_samples=1000):
    """Generates dummy data for training and testing."""
    X_grid = np.random.randint(0, 100, size=(num_samples, 50, 50)).astype(np.float32) / 100.0
    X_value = np.random.randint(0, 100, size=(num_samples, 1)).astype(np.float32) / 100.0
    y = np.random.rand(num_samples, 1).astype(np.float32)
    
    return X_grid, X_value, y

def train_agent(model, dataloader, epochs=10):
    """
    Trains the agent model using PyTorch's standard training loop.
    """
    print("Training the agent...")
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()
    
    model.train()  # Set the model to training mode
    
    for epoch in range(epochs):
        for grid_data, value_data, labels in dataloader:
            grid_data, value_data, labels = grid_data.to(device), value_data.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(grid_data.unsqueeze(1), value_data)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
        
        print(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")

def test_agent(model, grid, value):
    """
    Tests a trained PyTorch model with a single input.
    """
    model.eval()  # Set the model to evaluation mode
    with torch.no_grad():
        grid_tensor = torch.from_numpy(grid).float().unsqueeze(0).unsqueeze(0).to(device)
        value_tensor = torch.from_numpy(np.array([value])).float().unsqueeze(0).to(device)
        
        prediction = model(grid_tensor, value_tensor)
    
    return prediction.item()

def main():
    # --- Part 1: Build and Train the Agent ---
    
    # Instantiate the agent model and move it to the device
    agent_model = AgentModel().to(device)
    
    # Generate dummy data
    X_grid_data, X_value_data, y_output_data = generate_dummy_data()
    
    # Split data into training and validation sets
    X_grid_train, _, X_value_train, _, y_train, _ = train_test_split(
        X_grid_data, X_value_data, y_output_data, test_size=0.2, random_state=42)
        
    # Create DataLoader for training
    train_dataset = TensorDataset(
        torch.from_numpy(X_grid_train),
        torch.from_numpy(X_value_train),
        torch.from_numpy(y_train)
    )
    train_dataloader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    
    # Train the model
    train_agent(agent_model, train_dataloader, epochs=10)
    
    # Save the trained model's state
    torch.save(agent_model.state_dict(), 'trained_agent_model_pytorch.pth')
    print("Training complete. Model weights saved as 'trained_agent_model_pytorch.pth'.")
    
    # --- Part 2: Test the Trained Agent ---
    
    print("\n--- Testing the trained agent ---")
    
    # Example test inputs
    test_grid = np.random.randint(0, 100, size=(50, 50)) / 100.0
    test_value = np.random.randint(0, 100) / 100.0
    
    print(f"Test Grid (sample): \n{test_grid[:2, :2]}")
    print(f"Test Value: {test_value}")
    
    # Load the model for testing
    loaded_model = AgentModel().to(device)
    loaded_model.load_state_dict(torch.load('trained_agent_model_pytorch.pth'))
    
    # Get and print the prediction
    final_prediction = test_agent(loaded_model, test_grid, test_value)
    print(f"\nPredicted output (0-1 float): {final_prediction}")

if __name__ == "__main__":
    main()

