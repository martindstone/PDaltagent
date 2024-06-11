import {
  useCallback,
  useState,
} from 'react';
import {
    Modal,
    ModalOverlay,
    ModalContent,
    ModalHeader,
    ModalFooter,
    ModalBody,
    Button,
    Input,
    FormControl,
    FormLabel,
    useToast,
} from '@chakra-ui/react';

import { urlFor } from '../../util/helpers';

const ChangePasswordModal = ({ isOpen, onClose, email }) => {
    const toast = useToast();

    const [password, setPassword] = useState('');

    const handleChangePassword = useCallback((e) => {
        e.preventDefault();
        const csrfToken = sessionStorage.getItem('csrfToken');
        console.log('Changing password for user:', email);
        fetch(urlFor(`/users/${email}`), {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRF-TOKEN': csrfToken,
            },
            body: JSON.stringify({
              password,
            })
          }
        )
        .then((res) => res.json())
        .then((data) => {
            console.log('Response:', data);
            if (data?.status === 'ok') {
                toast({
                    title: 'Password changed',
                    status: 'success',
                    duration: 3000,
                    isClosable: true,
                });
                onClose();
            } else {
                toast({
                    title: `Failed to change password: ${data?.message || 'Unknown error'}`,
                    status: 'error',
                    duration: 3000,
                    isClosable: true,
                });
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            toast({
                title: `Failed to change password: ${error.message || 'Unknown error'}`,
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
        });
        onClose();
    }, [email, password, onClose, toast]);

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
                <ModalHeader>Change Password for {email}</ModalHeader>
                <form onSubmit={handleChangePassword}>
                    <ModalBody>
                        <FormControl>
                            <FormLabel>Password</FormLabel>
                            <Input placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
                        </FormControl>
                    </ModalBody>
                    <ModalFooter>
                        <Button type="submit" colorScheme="blue" mr={3} >
                            Change Password
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

export default ChangePasswordModal;
