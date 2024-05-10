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


const DeleteMaintenanceModal = ({ isOpen, onClose, record, setDataHasChanged }) => {
    const toast = useToast();

    const id = record?.id;
    const handleDeleteMaintenance = useCallback((e) => {
        e.preventDefault();
        const csrfToken = sessionStorage.getItem('csrfToken');
        console.log('Deleting maintenance:', id);
        fetch(`/maints/${id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRF-TOKEN': csrfToken,
            },
        })
        .then((res) => res.json())
        .then((data) => {
            console.log('Response:', data);
            if (data?.status === 'ok') {
                toast({
                    title: 'Maintenance window deleted',
                    status: 'success',
                    duration: 3000,
                    isClosable: true,
                });
                setDataHasChanged(true);
            } else {
                toast({
                    title: 'Failed to delete maintenance window',
                    status: 'error',
                    duration: 3000,
                    isClosable: true,
                });
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            toast({
                title: 'Failed to delete maintenance window',
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
        });
        onClose();
    }, [id, onClose, toast, setDataHasChanged]);

    if (!id) {
        return null;
    }

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
        >
            <ModalOverlay />
            <ModalContent>
                <ModalHeader>Delete Maintenance Window</ModalHeader>
                <form onSubmit={handleDeleteMaintenance}>
                    <ModalBody>
                        <Text>
                            Are you sure you want to delete this maintenance window?
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
