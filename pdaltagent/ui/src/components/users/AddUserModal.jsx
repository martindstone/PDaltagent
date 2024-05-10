import { useCallback, useEffect, useState } from 'react';
import {
    Modal,
    ModalOverlay,
    ModalContent,
    ModalHeader,
    ModalFooter,
    ModalBody,
    Input,
    Button,
    // Flex,
    FormControl,
    FormLabel,
    // Select,
    Text,
    useToast,
    Checkbox,
} from '@chakra-ui/react';

const AddUserModal = ({ isOpen, onClose }) => {
    const toast = useToast();

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [roles, setRoles] = useState(['user']);

    const [valid, setValid] = useState(false);
    const [validationHint, setValidationHint] = useState('');

    useEffect(() => {
        // setValid to true if all fields are filled
        if (
            email &&
            password &&
            roles
        ) {
            setValid(true);
            setValidationHint('');
        } else {
            setValid(false);
            if (!email) setValidationHint('Email is required');
            else if (!password) setValidationHint('Password is required');
        }
    }, [email, password, roles]);

    const clearState = useCallback(() => {
        setEmail('');
        setPassword('');
        setRoles(['user']);
    }, []);

    const handleAddUser = useCallback((e) => {
        e.preventDefault();
        const csrfToken = sessionStorage.getItem('csrfToken');
        fetch('/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRF-TOKEN': csrfToken,
            },
            body: JSON.stringify({
              email,
              password,
              roles,
            })
        })
        .then((res) => res.json())
        .then((data) => {
            if (data?.status === 'ok') {
                onClose();
                clearState();
                toast({
                    title: 'User added',
                    status: 'success',
                    duration: 3000,
                    isClosable: true,
                });
            } else {
                toast({
                    title: `Failed to add user: ${data?.message || 'Unknown error'}`,
                    status: 'error',
                    duration: 3000,
                    isClosable: true,
                });
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            toast({
                title: `Failed to add user: ${error.message || 'Unknown error'}`,
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
        });
    }, [email, password, roles, toast, onClose, clearState]);

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            size="xl"
        >
            <ModalOverlay />
            <ModalContent>
                <ModalHeader>Add a User</ModalHeader>
                <form onSubmit={handleAddUser}>
                    <ModalBody>
                        <FormControl>
                            <FormLabel>Email</FormLabel>
                            <Input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} isInvalid={!email} />
                        </FormControl>
                        <FormControl>
                            <FormLabel>Password</FormLabel>
                            <Input placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
                        </FormControl>
                        <FormControl>
                            <FormLabel>Admin</FormLabel>
                            <Checkbox isChecked={roles.includes('admin')} onChange={(e) => setRoles(e.target.checked ? [...roles, 'admin'] : roles.filter((role) => role !== 'admin'))} />
                        </FormControl>
                        {validationHint && (
                            <Text
                                display="block"
                                color="red"
                                fontSize="sm"
                                fontStyle="italic"
                                my={2}
                            >
                                {validationHint}
                            </Text>
                        )}
                    </ModalBody>
                    <ModalFooter>
                        <Button type="submit" colorScheme="blue" mr={3} isDisabled={!valid} >
                            Add User
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

export default AddUserModal;
