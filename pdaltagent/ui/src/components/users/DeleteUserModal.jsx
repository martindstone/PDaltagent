import { useCallback } from 'react';
import {
    Modal,
    ModalOverlay,
    ModalContent,
    ModalHeader,
    ModalFooter,
    ModalBody,
    Button,
    Text,
    useToast,
} from '@chakra-ui/react';

import { urlFor } from '../../util/helpers';

const DeleteMaintenanceModal = ({ isOpen, onClose, email }) => {
    const toast = useToast();

    const handleDeleteUser = useCallback((e) => {
        e.preventDefault();
        const csrfToken = sessionStorage.getItem('csrfToken');
        fetch(urlFor(`/users/${email}`), {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRF-TOKEN': csrfToken,
            },
        })
        .then((res) => res.json())
        .then((data) => {
            if (data?.status === 'ok') {
                toast({
                    title: 'User deleted',
                    status: 'success',
                    duration: 3000,
                    isClosable: true,
                });
                onClose()
            } else {
                toast({
                    title: `Failed to delete user: ${data?.message || 'Unknown error'}`,
                    status: 'error',
                    duration: 3000,
                    isClosable: true,
                });
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            toast({
                title: `Failed to delete user: ${error.message || 'Unknown error'}`,
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
        });
        onClose();
    }, [email, onClose, toast]);

    if (!email) {
        return null;
    }

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
        >
            <ModalOverlay />
            <ModalContent>
                <ModalHeader>Delete User</ModalHeader>
                <form onSubmit={handleDeleteUser}>
                    <ModalBody>
                        <Text>
                            Are you sure you want to delete
                            {' '}
                            {email}
                            ?
                        </Text>
                    </ModalBody>
                    <ModalFooter>
                        <Button type="submit" colorScheme="red" mr={3} >
                            Delete
                        </Button>
                        <Button onClick={onClose}>
                            Cancel
                        </Button>
                    </ModalFooter>
                </form>
            </ModalContent>
        </Modal>
    );
}

export default DeleteMaintenanceModal;
