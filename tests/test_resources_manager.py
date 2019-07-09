from unittest import TestCase
from unittest.mock import patch

from path import Path

from dakara_base.resources_manager import (
    generate_get_resource,
    get_file,
    ResourceNotFoundError,
    resource_listdir,
)


MODULE_PATH = Path(__file__).dirname().abspath()


class ResourceListdirTestCase(TestCase):
    """Test the `resource_listdir` function
    """

    @patch("dakara_base.resources_manager.resource_listdir_orig")
    def test_no_dunderscore(self, mock_resource_listdir_orig):
        """Test the function does not output entries with dunderscore
        """
        # mock the call
        mock_resource_listdir_orig.return_value = ["aaaa.file", "__init__.py"]

        # call the function
        result = resource_listdir("some path", "")

        # assert the call
        mock_resource_listdir_orig.assert_called_once_with("some path", "")

        # assert the result
        self.assertListEqual(result, ["aaaa.file"])


class GetFileTestCase(TestCase):
    """Test the `get_file` function
    """

    @patch("dakara_base.resources_manager.resource_filename")
    @patch("dakara_base.resources_manager.resource_exists")
    def test_success(self, mock_resource_exists, mock_resource_filename):
        """Test to get a file successfuly
        """
        # mock the call
        mock_resource_exists.return_value = True
        mock_resource_filename.return_value = "path to resource"

        # call the function
        result = get_file("my.module", "some resource")

        # assert the call
        mock_resource_exists.assert_called_once_with("my.module", "some resource")
        mock_resource_filename.assert_called_once_with("my.module", "some resource")

        # assert the result
        self.assertEqual(result, "path to resource")

    @patch("dakara_base.resources_manager.resource_filename")
    @patch("dakara_base.resources_manager.resource_exists")
    def test_fail(self, mock_resource_exists, mock_resource_filename):
        """Test to get a file that does not exist
        """
        # mock the call
        mock_resource_exists.return_value = False

        # call the function
        with self.assertRaises(ResourceNotFoundError) as error:
            get_file("my.module", "some resource")

        # assert the error
        self.assertEqual(
            str(error.exception), "File 'some resource' not found within resources"
        )

        # assert the call
        mock_resource_exists.assert_called_once_with("my.module", "some resource")
        mock_resource_filename.assert_not_called()

    def test_real(self):
        """Test to access a real file
        """
        # call the function
        result = get_file("tests.resources", "dummy")

        # assert the result
        path = MODULE_PATH / "resources" / "dummy"
        self.assertEqual(result, path.normpath())


class GenerateGetResourceTestCase(TestCase):
    """Test the `generate_get_resource` function factory
    """

    def setUp(self):
        # set up resource type
        self.resource_type = "resource type"

        # set up resource name
        self.resource_name = "some resource"

        # set up resource path
        self.resource_path = "path/to/some/resource"

        # set up resource getter
        self.get_resource = generate_get_resource(
            "resources.requirement", [self.resource_name], self.resource_type
        )

    def test_docstring(self):
        """Test the docstring of the generated function exists
        """
        self.assertIsNotNone(self.get_resource.__doc__)

    @patch("dakara_base.resources_manager.resource_filename")
    def test_sucess(self, mock_resource_filename):
        """Test to get a resource successfuly
        """
        # mock the call
        mock_resource_filename.return_value = self.resource_path

        # call the function
        result = self.get_resource(self.resource_name)

        # assert the call
        mock_resource_filename.assert_called_once_with(
            "resources.requirement", self.resource_name
        )

        # assert the result
        self.assertEqual(result, Path(self.resource_path).normpath())

    @patch("dakara_base.resources_manager.resource_filename")
    def test_fail(self, mock_resource_filename):
        """Test to get a resource that does not exist
        """
        # call the function
        with self.assertRaises(ResourceNotFoundError) as error:
            self.get_resource("none")

        # assert the error
        self.assertEqual(
            str(error.exception), "Resource type file 'none' not found within resources"
        )

        # assert the call
        mock_resource_filename.assert_not_called()
