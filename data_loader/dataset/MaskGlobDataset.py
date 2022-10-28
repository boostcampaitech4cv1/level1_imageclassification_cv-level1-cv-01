import os
import re
import glob
from torch.utils.data import Dataset
from PIL import Image

class MaskGlobDataset(Dataset):
    def __init__(self, root, transform, train=True):
        """
        csv 없이 파일 경로에서 라벨을 추출하는 데이터셋
        OfflineAug를 위해 제작함
        Args:
            root: 이미지가 들어있는 최상위 디렉터리
                  ex) '/opt/ml/input/data/train/images'
            transform:
            train:
        """
        self.root = root
        self.train = train
        self.transform = transform

        files = glob.glob(os.path.join(root, '**/*'), recursive=True)
        self.paths = [f for f in files if self._is_image(f)]
        self.labels = []

        if train:
            for p in self.paths:
                self.labels.append(self._parse(p))


    def _is_image(self, path):
        exts = ['jpg', 'jpeg', 'png']
        return any(path.endswith(ext) for ext in exts)


    def _parse(self, p):
        """
        path를 파싱해 라벨 리턴
        """
        match = re.search('_(.+)_Asian_(\d+)/(.*)[\.-]', p)
        if match and len(match.groups()) == 3:
            gender, age, mask = match.groups()
            gender = 0 if gender == 'male' else 1
            age = int(age)
            if age < 30:
                age = 0
            elif age < 60:
                age = 1
            else:
                age = 2

            if mask.startswith('normal'):
                mask = 2
            elif mask.startswith('incorrect'):
                mask = 1
            else:
                mask = 0
            return mask * 6 + gender * 3 + age
        else:
            raise Exception(f'Cannot parsing label from the path: {p}')


    def __getitem__(self, index):
        image = Image.open(self.paths[index])
        if self.transform:
            image = self.transform(image)
        if self.train:
            label = self.labels[index]
            return image, label
        return image, -1

    def __len__(self):
        return len(self.paths)