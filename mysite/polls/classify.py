import numpy as np
import torch
import torch.optim as optim
import torchvision.transforms as transforms
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from torch.utils.data.dataset import random_split
import math

max_classes = 90
class SELayer(nn.Module):
    def __init__(self, channel, reduction=16):
        super(SELayer, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channel, channel // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channel // reduction, channel, bias=False),
            nn.Sigmoid()
        )

    def forward(self, x):
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1, 1)
        return x * y.expand_as(x)


class Bottleneck(nn.Module):
    def __init__(self, inplanes, expansion=4, growthRate=12):
        super(Bottleneck, self).__init__()
        planes = expansion * growthRate
        self.bn1 = nn.BatchNorm2d(inplanes)
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.se = SELayer(planes)
        self.conv2 = nn.Conv2d(planes, growthRate, kernel_size=3,
                               padding=1, bias=False)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        out = self.bn1(x)
        out = self.relu(out)
        out = self.conv1(out)
        out = self.bn2(out)
        out = self.se(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = torch.cat((x, out), 1)
        return out


class BasicBlock(nn.Module):
    def __init__(self, inplanes, expansion=1, growthRate=12):
        super(BasicBlock, self).__init__()
        planes = expansion * growthRate
        self.bn1 = nn.BatchNorm2d(inplanes)
        self.conv1 = nn.Conv2d(inplanes, growthRate, kernel_size=3,
                               padding=1, bias=False)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        out = self.bn1(x)
        out = self.relu(out)
        out = self.conv1(out)
        out = torch.cat((x, out), 1)
        return out


class Transition(nn.Module):
    def __init__(self, inplanes, outplanes):
        super(Transition, self).__init__()
        self.bn1 = nn.BatchNorm2d(inplanes)
        self.conv1 = nn.Conv2d(inplanes, outplanes, kernel_size=1,
                               bias=False)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        out = self.bn1(x)
        out = self.relu(out)
        out = self.conv1(out)
        out = F.avg_pool2d(out, 2)
        return out


class DenseNet(nn.Module):

    def __init__(self, depth=10, block=Bottleneck,
                 num_classes=max_classes + 1, growthRate=12, compressionRate=2):
        super(DenseNet, self).__init__()
        n = (depth - 4) / 3 if block == BasicBlock else (depth - 4) // 6
        self.growthRate = growthRate
        self.inplanes = growthRate * 2
        self.conv1 = nn.Conv2d(3, self.inplanes, kernel_size=3, padding=1,
                               bias=False)
        self.dense1 = self.build_denseblock(block, n)
        self.trans1 = self.build_transition(compressionRate)
        self.dense2 = self.build_denseblock(block, n)
        self.trans2 = self.build_transition(compressionRate)
        self.dense3 = self.build_denseblock(block, n)
        self.bn = nn.BatchNorm2d(self.inplanes)
        self.relu = nn.ReLU(inplace=True)
        self.avgpool = nn.AvgPool2d(8)
        self.fc = nn.Linear(self.inplanes, num_classes)
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2. / n))
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    def build_denseblock(self, block, blocks):
        layers = []
        for i in range(blocks):
            layers.append(block(self.inplanes, growthRate=self.growthRate))
            self.inplanes += self.growthRate
        return nn.Sequential(*layers)

    def build_transition(self, compressionRate):
        inplanes = self.inplanes
        outplanes = int(math.floor(self.inplanes // compressionRate))
        self.inplanes = outplanes
        return Transition(inplanes, outplanes)

    def forward(self, x):
        x = self.conv1(x)
        x = self.trans1(self.dense1(x))
        x = self.trans2(self.dense2(x))
        x = self.dense3(x)
        x = self.bn(x)
        x = self.relu(x)
        x = self.avgpool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x


def densenet151():
    return DenseNet(depth=151)

def def_classify():
    model = torch.load('../models/cifar100/2017315471.pt')
    print(model)


if __name__ == "__main__":
    model = torch.load('../models/cifar100/2017315471.pt')
    model.load_state_dict(torch.load("../models/model_2017315471.pth"))
