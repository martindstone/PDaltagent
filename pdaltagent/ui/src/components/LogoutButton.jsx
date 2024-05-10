import {
    Button,
} from "@chakra-ui/react";

const LogoutButton = () => {
    const handleLogout = () => {
        fetch('/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        })
        .then((res) => {
            if (res.ok) {
                window.location.reload();
            }
        });
    };

    return (
        <Button onClick={handleLogout}>Logout</Button>
    );
}

export default LogoutButton;