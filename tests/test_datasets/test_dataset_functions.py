import unittest
import os
import os
import sys

if sys.version_info[0] >= 3:
    from unittest import mock
else:
    import mock

from oslo_concurrency import lockutils
import scipy.sparse

import openml
from openml import OpenMLDataset
from openml.exceptions import OpenMLCacheException, PyOpenMLError
from openml.testing import TestBase

from openml.datasets.functions import (_get_cached_dataset,
                                       _get_cached_dataset_features,
                                       _get_cached_dataset_qualities,
                                       _get_cached_datasets,
                                       _get_dataset_description,
                                       _get_dataset_arff,
                                       _get_dataset_features,
                                       _get_dataset_qualities)


class TestOpenMLDataset(TestBase):
    _multiprocess_can_split_ = True

    def setUp(self):
        super(TestOpenMLDataset, self).setUp()

    def tearDown(self):
        self._remove_pickle_files()
        super(TestOpenMLDataset, self).tearDown()

    def _remove_pickle_files(self):
        cache_dir = self.static_cache_dir
        for did in ['-1', '2']:
            with lockutils.external_lock(
                    name='datasets.functions.get_dataset:%s' % did,
                    lock_path=os.path.join(openml.config.get_cache_directory(), 'locks'),
            ):
                pickle_path = os.path.join(cache_dir, 'datasets', did,
                                           'dataset.pkl')
                try:
                    os.remove(pickle_path)
                except:
                    pass

    def test__list_cached_datasets(self):
        openml.config.set_cache_directory(self.static_cache_dir)
        cached_datasets = openml.datasets.functions._list_cached_datasets()
        self.assertIsInstance(cached_datasets, list)
        self.assertEqual(len(cached_datasets), 2)
        self.assertIsInstance(cached_datasets[0], int)

    @mock.patch('openml.datasets.functions._list_cached_datasets')
    def test__get_cached_datasets(self, _list_cached_datasets_mock):
        openml.config.set_cache_directory(self.static_cache_dir)
        _list_cached_datasets_mock.return_value = [-1, 2]
        datasets = _get_cached_datasets()
        self.assertIsInstance(datasets, dict)
        self.assertEqual(len(datasets), 2)
        self.assertIsInstance(list(datasets.values())[0], OpenMLDataset)

    def test__get_cached_dataset(self, ):
        openml.config.set_cache_directory(self.static_cache_dir)
        dataset = _get_cached_dataset(2)
        features = _get_cached_dataset_features(2)
        qualities = _get_cached_dataset_qualities(2)
        self.assertIsInstance(dataset, OpenMLDataset)
        self.assertTrue(len(dataset.features) > 0)
        self.assertTrue(len(dataset.features) == len(features['oml:feature']))
        self.assertTrue(len(dataset.qualities) == len(qualities['oml:quality']))

    def test_get_cached_dataset_description(self):
        openml.config.set_cache_directory(self.static_cache_dir)
        description = openml.datasets.functions._get_cached_dataset_description(2)
        self.assertIsInstance(description, dict)

    def test_get_cached_dataset_description_not_cached(self):
        openml.config.set_cache_directory(self.static_cache_dir)
        self.assertRaisesRegexp(OpenMLCacheException, "Dataset description for "
                                                      "dataset id 3 not cached",
                                openml.datasets.functions._get_cached_dataset_description,
                                3)

    def test_get_cached_dataset_arff(self):
        openml.config.set_cache_directory(self.static_cache_dir)
        description = openml.datasets.functions._get_cached_dataset_arff(
            dataset_id=2)
        self.assertIsInstance(description, str)

    def test_get_cached_dataset_arff_not_cached(self):
        openml.config.set_cache_directory(self.static_cache_dir)
        self.assertRaisesRegexp(OpenMLCacheException, "ARFF file for "
                                                      "dataset id 3 not cached",
                                openml.datasets.functions._get_cached_dataset_arff,
                                3)

    def test_list_datasets(self):
        # We can only perform a smoke test here because we test on dynamic
        # data from the internet...
        datasets = openml.datasets.list_datasets()
        # 1087 as the number of datasets on openml.org
        self.assertGreaterEqual(len(datasets), 100)
        for did in datasets:
            self._check_dataset(datasets[did])

    def test_list_datasets_by_tag(self):
        datasets = openml.datasets.list_datasets(tag='study_14')
        self.assertGreaterEqual(len(datasets), 100)
        for did in datasets:
            self._check_dataset(datasets[did])

    def test_list_datasets_paginate(self):
        size = 10
        max = 100
        for i in range(0, max, size):
            datasets = openml.datasets.list_datasets(offset=i, size=size)
            self.assertGreaterEqual(size, len(datasets))
            for did in datasets:
                self._check_dataset(datasets[did])

    @unittest.skip('See https://github.com/openml/openml-python/issues/149')
    def test_check_datasets_active(self):
        active = openml.datasets.check_datasets_active([1, 17])
        self.assertTrue(active[1])
        self.assertFalse(active[17])
        self.assertRaisesRegexp(ValueError, 'Could not find dataset 79 in OpenML'
                                            ' dataset list.',
                                openml.datasets.check_datasets_active, [79])

    def test_get_datasets(self):
        dids = [1, 2]
        datasets = openml.datasets.get_datasets(dids)
        self.assertEqual(len(datasets), 2)
        self.assertTrue(os.path.exists(os.path.join(
            openml.config.get_cache_directory(), "datasets", "1", "description.xml")))
        self.assertTrue(os.path.exists(os.path.join(
            openml.config.get_cache_directory(), "datasets", "2", "description.xml")))
        self.assertTrue(os.path.exists(os.path.join(
            openml.config.get_cache_directory(), "datasets", "1", "dataset.arff")))
        self.assertTrue(os.path.exists(os.path.join(
            openml.config.get_cache_directory(), "datasets", "2", "dataset.arff")))
        self.assertTrue(os.path.exists(os.path.join(
            openml.config.get_cache_directory(), "datasets", "1", "features.xml")))
        self.assertTrue(os.path.exists(os.path.join(
            openml.config.get_cache_directory(), "datasets", "2", "features.xml")))
        self.assertTrue(os.path.exists(os.path.join(
            openml.config.get_cache_directory(), "datasets", "1", "qualities.xml")))
        self.assertTrue(os.path.exists(os.path.join(
            openml.config.get_cache_directory(), "datasets", "2", "qualities.xml")))

    def test_get_dataset(self):
        dataset = openml.datasets.get_dataset(1)
        self.assertEqual(type(dataset), OpenMLDataset)
        self.assertEqual(dataset.name, 'anneal')
        self.assertTrue(os.path.exists(os.path.join(
            openml.config.get_cache_directory(), "datasets", "1", "description.xml")))
        self.assertTrue(os.path.exists(os.path.join(
            openml.config.get_cache_directory(), "datasets", "1", "dataset.arff")))
        self.assertTrue(os.path.exists(os.path.join(
            openml.config.get_cache_directory(), "datasets", "1", "features.xml")))
        self.assertTrue(os.path.exists(os.path.join(
            openml.config.get_cache_directory(), "datasets", "1", "qualities.xml")))

        self.assertGreater(len(dataset.features), 1)
        self.assertGreater(len(dataset.qualities), 4)

    def test_get_dataset_with_string(self):
        dataset = openml.datasets.get_dataset(101)
        self.assertRaises(PyOpenMLError, dataset._get_arff, 'arff')
        self.assertRaises(PyOpenMLError, dataset.get_data)

    def test_get_dataset_sparse(self):
        dataset = openml.datasets.get_dataset(102)
        X = dataset.get_data()
        self.assertIsInstance(X, scipy.sparse.csr_matrix)

    def test_download_rowid(self):
        # Smoke test which checks that the dataset has the row-id set correctly
        did = 44
        dataset = openml.datasets.get_dataset(did)
        self.assertEqual(dataset.row_id_attribute, 'Counter')

    def test__get_dataset_description(self):
        description = _get_dataset_description(self.workdir, 2)
        self.assertIsInstance(description, dict)
        description_xml_path = os.path.join(self.workdir,
                                            'description.xml')
        self.assertTrue(os.path.exists(description_xml_path))

    def test__getarff_path_dataset_arff(self):
        openml.config.set_cache_directory(self.static_cache_dir)
        description = openml.datasets.functions._get_cached_dataset_description(2)
        arff_path = _get_dataset_arff(self.workdir, description)
        self.assertIsInstance(arff_path, str)
        self.assertTrue(os.path.exists(arff_path))

    def test__get_dataset_features(self):
        features = _get_dataset_features(self.workdir, 2)
        self.assertIsInstance(features, dict)
        features_xml_path = os.path.join(self.workdir, 'features.xml')
        self.assertTrue(os.path.exists(features_xml_path))

    def test__get_dataset_qualities(self):
        # Only a smoke check
        qualities = _get_dataset_qualities(self.workdir, 2)
        self.assertIsInstance(qualities, dict)

    def test_deletion_of_cache_dir(self):
        # Simple removal
        did_cache_dir = openml.datasets.functions.\
            _create_dataset_cache_directory(1)
        self.assertTrue(os.path.exists(did_cache_dir))
        openml.datasets.functions._remove_dataset_cache_dir(did_cache_dir)
        self.assertFalse(os.path.exists(did_cache_dir))

    # Use _get_dataset_arff to load the description, trigger an exception in the
    # test target and have a slightly higher coverage
    @mock.patch('openml.datasets.functions._get_dataset_arff')
    def test_deletion_of_cache_dir_faulty_download(self, patch):
        patch.side_effect = Exception('Boom!')
        self.assertRaisesRegexp(Exception, 'Boom!', openml.datasets.get_dataset,
                                1)
        datasets_cache_dir = os.path.join(self.workdir, 'datasets')
        self.assertEqual(len(os.listdir(datasets_cache_dir)), 0)

    def test_publish_dataset(self):
        dataset = openml.datasets.get_dataset(3)
        file_path = os.path.join(openml.config.get_cache_directory(),
                                 "datasets", "3", "dataset.arff")
        dataset = OpenMLDataset(
            name="anneal", version=1, description="test",
            format="ARFF", licence="public", default_target_attribute="class", data_file=file_path)
        dataset.publish()
        self.assertIsInstance(dataset.dataset_id, int)

    def test__retrieve_class_labels(self):
        openml.config.set_cache_directory(self.static_cache_dir)
        labels = openml.datasets.get_dataset(2).retrieve_class_labels()
        self.assertEqual(labels, ['1', '2', '3', '4', '5', 'U'])
        labels = openml.datasets.get_dataset(2).retrieve_class_labels(
            target_name='product-type')
        self.assertEqual(labels, ['C', 'H', 'G'])

    def test_upload_dataset_with_url(self):
        dataset = OpenMLDataset(
            name="UploadTestWithURL", version=1, description="test",
            format="ARFF",
            url="https://www.openml.org/data/download/61/dataset_61_iris.arff")
        dataset.publish()
        self.assertIsInstance(dataset.dataset_id, int)
