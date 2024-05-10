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
    // ModalCloseButton,
    Input,
    Button,
    FormControl,
    FormLabel,
    useToast,
  } from '@chakra-ui/react';

const LoginModal = ({ isOpen, onClose }) => {
    const toast = useToast();

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const handleLogin = useCallback((e) => {
        e.preventDefault();
        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ email, password })
        })
        .then((res) => {
            if (res.ok) {
                onClose();
                toast({
                    title: 'Login successful',
                    status: 'success',
                    duration: 3000,
                    isClosable: true,
                });
            } else {
                toast({
                    title: 'Login failed',
                    status: 'error',
                    duration: 3000,
                    isClosable: true,
                });
            }
        });
    }, [email, password, onClose, toast]);

    return (
        <Modal isOpen={isOpen} onClose={onClose}>
            <ModalOverlay />
            <ModalContent>
                <ModalHeader>Login</ModalHeader>
                <form onSubmit={handleLogin}>
                    <ModalBody>
                        <FormControl>
                            <FormLabel>Email</FormLabel>
                            <Input placeholder="Email" onChange={(e) => setEmail(e.target.value)}/>
                        </FormControl>
                        <FormControl>
                            <FormLabel>Password</FormLabel>
                            <Input
                                type="password"
                                placeholder="Password"
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </FormControl>
                    </ModalBody>
                    <ModalFooter>
                        <Button
                            type="submit"
                            colorScheme="blue"
                            mr={3}
                        >
                            Login
                        </Button>
                    </ModalFooter>
                </form>
            </ModalContent>
        </Modal>
    );
}

export default LoginModal;
