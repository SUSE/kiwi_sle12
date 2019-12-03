import mock
from mock import patch
from pytest import raises
from collections import namedtuple

from kiwi.system.kernel import Kernel

from kiwi.exceptions import KiwiKernelLookupError


class TestKernel:
    @patch('os.listdir')
    def setup(self, mock_listdir):
        mock_listdir.return_value = ['1.2.3-default']
        self.kernel = Kernel('root-dir')
        assert self.kernel.kernel_names == [
            'vmlinux',
            'vmlinuz',
            'uImage-1.2.3-default',
            'Image-1.2.3-default',
            'zImage-1.2.3-default',
            'vmlinuz-1.2.3-default',
            'vmlinux-1.2.3-default',
            'image-1.2.3-default'
        ]

    def test_get_kernel_raises_if_no_kernel_found(self):
        self.kernel.kernel_names = []
        with raises(KiwiKernelLookupError):
            self.kernel.get_kernel(raise_on_not_found=True)

    @patch('os.path.exists')
    @patch('os.path.realpath')
    @patch('kiwi.command.Command.run')
    def test_get_kernel(self, mock_run, mock_realpath, mock_os):
        run = namedtuple(
            'run', ['output']
        )
        result = run(output='42')
        mock_os.return_value = True
        mock_run.return_value = result
        mock_realpath.return_value = 'vmlinux-realpath'
        data = self.kernel.get_kernel()
        mock_run.assert_called_once_with(
            command=['kversion', 'root-dir/boot/vmlinux-1.2.3-default.gz'],
            raise_on_error=False
        )
        assert data.filename == 'root-dir/boot/vmlinux'
        assert data.version == '42'
        assert data.name == 'vmlinux-realpath'

    @patch('os.path.exists')
    @patch('os.path.realpath')
    @patch('kiwi.command.Command.run')
    def test_get_kernel_from_arbitrary_kernel_image(
        self, mock_run, mock_realpath, mock_os
    ):
        def path_exists(path):
            return False if 'vmlinux.gz' in path else True

        self.kernel.kernel_names = ['zImage']
        run = namedtuple(
            'run', ['output']
        )
        result = run(output='42')
        mock_os.side_effect = path_exists
        mock_run.return_value = result
        mock_realpath.return_value = 'vmlinux.gz'
        data = self.kernel.get_kernel()
        mock_run.assert_called_once_with(
            command=['kversion', 'root-dir/boot/zImage'],
            raise_on_error=False
        )
        assert data.filename == 'root-dir/boot/zImage'
        assert data.version == '42'
        assert data.name == mock_realpath.return_value

    @patch('os.path.exists')
    @patch('kiwi.command.Command.run')
    def test_get_kernel_no_version(self, mock_run, mock_os):
        run = namedtuple(
            'run', ['output']
        )
        result = run(output=None)
        mock_os.return_value = True
        mock_run.return_value = result
        data = self.kernel.get_kernel()
        mock_run.assert_called_once_with(
            command=['kversion', 'root-dir/boot/vmlinux-1.2.3-default.gz'],
            raise_on_error=False
        )
        assert data.filename == 'root-dir/boot/vmlinux'
        assert data.version == 'no-version-found'

    @patch('os.path.exists')
    def test_get_xen_hypervisor(self, mock_os):
        mock_os.return_value = True
        data = self.kernel.get_xen_hypervisor()
        assert data.filename == 'root-dir/boot/xen.gz'
        assert data.name == 'xen.gz'

    @patch('kiwi.system.kernel.Kernel.get_kernel')
    @patch('kiwi.command.Command.run')
    def test_copy_kernel(self, mock_run, mock_get_kernel):
        result = mock.MagicMock()
        result.version = '42'
        result.filename = 'kernel'
        mock_get_kernel.return_value = result
        self.kernel.copy_kernel('target-dir')
        mock_run.assert_called_once_with(
            ['cp', 'kernel', 'target-dir/kernel-42.kernel']
        )

    @patch('kiwi.system.kernel.Kernel.get_xen_hypervisor')
    @patch('kiwi.command.Command.run')
    def test_copy_xen_hypervisor(self, mock_run, mock_get_xen):
        result = mock.MagicMock()
        result.name = 'xen.gz'
        result.filename = 'some/xen.gz'
        mock_get_xen.return_value = result
        self.kernel.copy_xen_hypervisor('target-dir')
        mock_run.assert_called_once_with(
            ['cp', 'some/xen.gz', 'target-dir/hypervisor-xen.gz']
        )
