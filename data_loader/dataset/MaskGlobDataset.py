import os
import re
import glob
from pathlib import Path
from torch.utils.data import Dataset
from PIL import Image

class MaskGlobDataset(Dataset):
    def __init__(self, root, transform, train=True, valid=False, paths=None):
        """
        csv 없이 파일 경로에서 라벨을 추출하는 데이터셋
        OfflineAug를 위해 제작함
        Args:
            root: 이미지가 들어있는 최상위 디렉터리
                  ex) '/opt/ml/input/data/train'
            transform:
            train: 미지원
            valid: valid 면 Offline Augmentatino 제외
            paths: 데이터셋 포함시키기 원하는 인물 directory path. 기본적 동작은 모두 glob
        """
        assert train == True

        self.root = root = Path(root)
        self.transform = transform
        self.train = train
        self.valid = valid

        self.paths = []
        self.labels = []

        if paths is None:
            files = root.glob('**/*')
            self.paths = [f for f in files if self._check_path(f)]
        else:
            for path in paths:
                files = (root / 'images' / path).glob('*.*')
                files = [f for f in files if self._check_path(f)]
                self.paths.extend(files)

        if train:
            for p in self.paths:
                self.labels.append(self._parse(p))


    def _check_path(self, path):
        # if self.valid and '-' in path.name:
        #     return False
        return self._is_image(path)


    def _is_image(self, path):
        exts = ['jpg', 'jpeg', 'png']
        p = str(path)
        return '._' not in p and any(p.endswith(ext) for ext in exts)


    def _parse(self, p):
        """
        path를 파싱해 라벨 리턴
        """
        p = str(p)
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
            raise Exception(f'Cannot parse label from the path: {p}')


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