import {
  useEffect,
  useState,
  useCallback,
} from 'react';

import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Checkbox,
  Button,
  useDisclosure,
  useToast,
  Box,
} from '@chakra-ui/react';

import {
  DeleteIcon,
  UnlockIcon,
} from '@chakra-ui/icons';

import { urlFor } from '../../util/helpers';

import AddUserModal from './AddUserModal';
import DeleteUserModal from './DeleteUserModal';
import ChangePasswordModal from './ChangePasswordModal';

const UserModal = ({
  isOpen,
  onClose,
  isAdmin,
}) => {
  const toast = useToast();
  const { isOpen: isAddOpen, onOpen: onAddOpen, onClose: onAddClose } = useDisclosure();
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure();
  const { isOpen: isChangePasswordOpen, onOpen: onChangePasswordOpen, onClose: onChangePasswordClose } = useDisclosure();

  const [users, setUsers] = useState([]);
  const [userToDelete, setUserToDelete] = useState(null);
  const [userToChangePassword, setUserToChangePassword] = useState(null);

  const fetchUsers = useCallback(() => {
    fetch(urlFor('/users'), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
      })
      .then((res) => res.json())
      .then((data) => {
        setUsers(data);
      })
      .catch((error) => {
        console.error('Error:', error);
      }
    );
  }, [setUsers]);

  useEffect(() => {
    if (isOpen) {
      fetchUsers();
    }
  }, [fetchUsers, isOpen]);

  const handleAddClose = useCallback(() => {
    onAddClose();
    fetchUsers();
  }, [onAddClose, fetchUsers]);

  const handleDelete = useCallback((email) => {
    setUserToDelete(email);
    onDeleteOpen();
  }, [onDeleteOpen]);

  const handleDeleteClose = useCallback(() => {
    onDeleteClose();
    fetchUsers();
  }, [onDeleteClose, fetchUsers]);

  const handleChangePassword = useCallback((email) => {
    setUserToChangePassword(email);
    onChangePasswordOpen();
  }, [onChangePasswordOpen]);

  const handleChangePasswordClose = useCallback(() => {
    onChangePasswordClose();
    fetchUsers();
  }, [onChangePasswordClose, fetchUsers]);

  const handleRoleChange = (email, isAdmin) => {
    const roles = isAdmin ? ['user', 'admin'] : ['user'];
    fetch(urlFor(`/users/${email}`), {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-CSRF-TOKEN': sessionStorage.getItem('csrfToken'),
      },
      body: JSON.stringify({
        roles,
      })
    })
    .then((res) => res.json())
    .then((data) => {
      if (data?.status === 'ok') {
        toast({
          title: 'User roles updated',
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
        fetchUsers();
      } else {
        toast({
          title: `Failed to update user roles: ${data?.message || 'Unknown error'}`,
          status: 'error',
          duration: 3000,
          isClosable: true,
        });
      }
    })
    .catch((error) => {
      toast({
        title: `Failed to update user roles: ${error.message || 'Unknown error'}`,
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    });
  };

  return (
    <>
      <Modal isOpen={isOpen} onClose={onClose} size="xxl" height="80%">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Users</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Box maxH="60%" overflowY="auto">
              <Table variant="striped">
                <Thead>
                  <Tr>
                    <Th>Email</Th>
                    <Th>Admin</Th>
                    <Th>Change Password</Th>
                    <Th>Delete</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {users.map((user) => (
                    <Tr key={user.email}>
                      <Td>{user.email}</Td>
                      <Td>
                        <Checkbox
                          isDisabled={!isAdmin}
                          isChecked={user.roles.includes('admin')}
                          onChange={(e) => handleRoleChange(user.email, e.target.checked)}
                        />
                      </Td>
                      <Td>
                        <Button isDisabled={!isAdmin} colorScheme="blue" onClick={() => handleChangePassword(user.email)}>
                          <UnlockIcon />
                        </Button>
                      </Td>
                      <Td>
                        <Button isDisabled={!isAdmin} colorScheme="red" onClick={() => handleDelete(user.email)}>
                          <DeleteIcon />
                        </Button>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </Box>
          </ModalBody>
          <ModalFooter>
            <Button mr={2} colorScheme="blue" onClick={onAddOpen}>
              Add User
            </Button>
            <Button onClick={onClose}>
              Done
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
      <AddUserModal isOpen={isAddOpen} onClose={handleAddClose} />
      <DeleteUserModal isOpen={isDeleteOpen} onClose={handleDeleteClose} email={userToDelete} />
      <ChangePasswordModal isOpen={isChangePasswordOpen} onClose={handleChangePasswordClose} email={userToChangePassword} />
    </>
  );
};

export default UserModal;
