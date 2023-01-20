from tqdm import tqdm
import csv
import os
import subprocess

import numpy as np
from sklearn.datasets import make_blobs
from mnist import MNIST

def get_dataset(dataset_type, n_points=1000, D=50, num_centers=10, k=20):
    if dataset_type == 'blobs':
        return make_blobs(n_points, D, centers=num_centers)
    elif dataset_type == 'single_blob':
        return make_blobs(n_points, D, centers=1)
    elif dataset_type == 'artificial':
        return get_artificial_dataset(n_points, D)
    elif dataset_type == 'mnist':
        return load_mnist()
    elif dataset_type == 'song':
        return load_song()
    elif dataset_type == 'cover_type':
        return load_cover_type()
    elif dataset_type == 'kdd_cup':
        return load_darpa_kdd_cup()
    elif dataset_type == 'census':
        return load_census_data()
    elif dataset_type == 'benchmark':
        return load_coreset_benchmark(k)
    else:
        raise ValueError('Dataset not implemented')

def get_artificial_dataset(n_points, D):
    g_points = np.ones([n_points, D])
    g_points[0] = -1000 * np.ones(D)
    g_points += np.random.rand(n_points, D)
    return g_points, np.ones(n_points)

def remap_features(points, columns):
    """ Move from categorical inputs to continuous, normalized data """
    new_points = np.zeros(points.shape)
    for c in range(columns):
        column = points[:, c]
        _, column_remap = np.unique(column, return_inverse=True)
        column_remap = column_remap.astype(np.float32)
        if np.max(column_remap) != 0:
            column_remap /= np.max(column_remap)
        new_points[:, c] = column_remap
    return new_points

def load_categorical_dataset(
    data_path,
    pickled_path,
    rows,
    columns,
    data_type,
    start_index=0,
    end_index=None
):
    if os.path.exists(pickled_path):
        dataset = np.load(pickled_path, allow_pickle=True)[()]
        return dataset['points'], dataset['labels']
    print('Could not find pickled dataset at {}. Loading from txt file and pickling...'.format(pickled_path))

    points = np.empty([rows, columns], dtype=data_type)
    labels = np.zeros([rows])
    if end_index is None:
        end_index = columns
    with open(data_path, 'r') as f:
        reader = csv.reader(f)
        for i, line in tqdm(enumerate(reader), total=rows):
            points[i] = np.array(line)[start_index:end_index]

    points = remap_features(points, columns)
    # If there are duplicate points, the HST will recur until segmentation fault
    points += np.random.rand(rows, columns) / 100000
    _, labels = np.unique(labels, return_inverse=True)
    np.save(pickled_path, {'points': points, 'labels': labels})
    return points, labels

def load_census_data():
    # Adult census data found at https://archive.ics.uci.edu/ml/datasets/census+income
    directory = os.path.join('data', 'census')
    data_path = os.path.join(directory, 'adult.data')
    pickled_path = os.path.join(directory, 'pickled_census.npy')
    rows, columns = 48842, 14
    data_type = str
    end_index = -1
    return load_categorical_dataset(
        data_path,
        pickled_path,
        rows,
        columns,
        data_type,
        end_index=end_index
    )

def load_darpa_kdd_cup():
    # 1999 KDD Cup dataset found at
    # https://www.kaggle.com/datasets/galaxyh/kdd-cup-1999-data?resource=download 
    directory = os.path.join('data', 'kdd_cup')
    data_path = os.path.join(directory, 'kddcup.data_10_percent', 'kddcup.data_10_percent')
    pickled_path = os.path.join(directory, 'pickled_kdd_cup.npy')
    rows, columns = 494021, 41
    data_type = str
    end_index = -1
    return load_categorical_dataset(
        data_path,
        pickled_path,
        rows,
        columns,
        data_type,
        end_index=end_index
    )

def load_cover_type():
    # Cover type dataset found at https://archive.ics.uci.edu/ml/datasets/covertype
    directory = os.path.join('data', 'cover_type')
    data_path = os.path.join(directory, 'covtype.data')
    pickled_path = os.path.join(directory, 'pickled_cover_type.npy')
    rows, columns = 581012, 54
    data_type = np.float32
    start_index = 1
    return load_categorical_dataset(
        data_path,
        pickled_path,
        rows,
        columns,
        data_type,
        start_index=start_index
    )


def load_song():
    # Million song dataset found at https://archive.ics.uci.edu/ml/datasets/yearpredictionmsd
    directory = os.path.join('data', 'song')
    pickled_path = os.path.join(directory, 'pickled_song.npy')
    if os.path.exists(pickled_path):
        dataset = np.load(pickled_path, allow_pickle=True)[()]
        return dataset['points'], dataset['labels']
    print('Could not find pickled dataset at {}. Loading from txt file and pickling...'.format(pickled_path))

    data_path = os.path.join('data', 'song', 'YearPredictionMSD.txt')
    rows, columns = 515345, 90
    points = np.zeros([rows, columns])
    labels = np.zeros([rows])
    with open(data_path, 'r') as f:
        reader = csv.reader(f)
        for i, line in tqdm(enumerate(reader), total=rows):
            points[i] = [float(p) for p in line[1:]]
            labels[i] = line[0]

    _, labels = np.unique(labels, return_inverse=True)
    # If there are duplicate points, the HST will recur until segmentation fault
    # So add tiny noise to put duplicate points in different HST branches
    points += np.random.rand(rows, columns) / 100000
    np.save(pickled_path, {'points': points, 'labels': labels})
    return points, labels

def load_mnist():
    mnist_data_path = os.path.join('data', 'mnist')
    if not os.path.isdir(mnist_data_path):
        subprocess.call(os.path.join('experiment_utils', 'get_mnist.sh'))

    mndata = MNIST(mnist_data_path)
    points, labels = mndata.load_training()
    points = np.array(points, dtype=np.float32)
    labels = np.array(labels)
    return points, labels

def load_coreset_benchmark(k, alpha=3):
    # Arbitrarily split up k into three sections with denominators that are mutually prime
    k_one = int(k / 5)
    k_two = int((k - k_one) / 3)
    k_three = int(k - k_one - k_two)
    benchmark_matrices = []
    for k in [k_one, k_two, k_three]:
        matrix = -1 * np.ones([k, k]) / k
        matrix += np.eye(k)

        columns = [matrix]
        for a in range(1, alpha):
            matrix_sections = np.split(columns[-1], k, axis=0)
            stretched_matrix = []
            for section in matrix_sections:
                for copy in range(k):
                    stretched_matrix.append(section)
            stretched_matrix = np.squeeze(np.concatenate(stretched_matrix, axis=0))
            columns.append(stretched_matrix)
        num_rows = len(columns[-1])
        
        equal_size_columns = []
        for column in columns:
            num_copies = int(num_rows / len(column))
            equal_size_column = np.concatenate([column for _ in range(num_copies)], axis=0)
            equal_size_columns.append(equal_size_column)
        benchmark_matrix = np.concatenate(equal_size_columns, axis=1)

        # Add a random vector offset to each benchmark dataset
        offset = np.sin(k) * k ** 2
        benchmark_matrix += offset

        benchmark_matrices.append(benchmark_matrix)

    padded_benchmarks = []
    sizes = [bm.shape[1] for bm in benchmark_matrices]
    for i, benchmark_matrix in enumerate(benchmark_matrices):
        pad_amount = max(sizes) - sizes[i]
        npad = ((0, 0), (0, pad_amount))
        padded = np.pad(benchmark_matrix, pad_width=npad, mode='constant', constant_values=0)
        padded_benchmarks.append(padded)

    padded_benchmarks = np.concatenate(padded_benchmarks, axis=0)
    return padded_benchmarks, np.ones(len(padded_benchmarks))