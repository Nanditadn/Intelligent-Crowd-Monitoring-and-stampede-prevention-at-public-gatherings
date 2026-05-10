# csrnet.py
# Real CSRNet loader for your existing project

import torch
import cv2
from torchvision import transforms
from model import CSRNet

device = "cpu"

# ---------------------------------------
# Load CSRNet model
# ---------------------------------------
net = CSRNet()

checkpoint = torch.load(
    "models/csrnet.pth",
    map_location=device
)

# Remove DataParallel "module." prefix
weights = {
    k.replace("module.", ""): v
    for k, v in checkpoint["state_dict"].items()
}

net.load_state_dict(weights)

net.eval()


# ---------------------------------------
# Image Transform
# ---------------------------------------
transform = transforms.Compose([
    transforms.ToTensor()
])


# ---------------------------------------
# Crowd Count Function
# ---------------------------------------
def csr_count(frame):

    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    tensor = transform(rgb).unsqueeze(0)

    with torch.no_grad():
        output = net(tensor)

    count = int(output.sum().item())

    if count < 0:
        count = 0

    return count