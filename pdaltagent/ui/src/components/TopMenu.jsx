import {
    Menu,
    MenuButton,
    MenuList,
    MenuItem,
    IconButton,
} from '@chakra-ui/react'

import {
    HamburgerIcon,
} from '@chakra-ui/icons'

import {
    urlFor,
} from '../util/helpers';

const TopMenu = ({
    toast,
    setNeedsRefresh,
    openAddUserModal,
}) => {
    const handleLogout = () => {
        fetch(urlFor('/logout'), {
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

    const handleRestart = () => {
        const csrfToken = sessionStorage.getItem('csrfToken');
        fetch(urlFor('/restart'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRF-TOKEN': csrfToken,
            }
        })
        .then((res) => {
            if (res.ok) {
                toast({
                    title: 'Services restarted',
                    status: 'success',
                    duration: 3000,
                    isClosable: true,
                });
                setNeedsRefresh(true);
            } else {
                toast({
                    title: 'Failed to restart services',
                    status: 'success',
                    duration: 3000,
                    isClosable: true,
                });
            }
        })
        .catch((error) => {
            toast({
                title: 'Failed to restart services',
                description: error,
                status: 'success',
                duration: 3000,
                isClosable: true,
            });
        });
    }
    return (
        <Menu>
            <MenuButton
                m={2}
                as={IconButton}
                aria-label='Options'
                icon={<HamburgerIcon />}
                variant='outline'
            />
            <MenuList>
                <MenuItem onClick={openAddUserModal}>
                    Users...
                </MenuItem>
                <MenuItem onClick={handleRestart}>
                    Restart PDaltagent services
                </MenuItem>
                <MenuItem onClick={handleLogout}>
                    Logout
                </MenuItem>
            </MenuList>
        </Menu>
    )
}

export default TopMenu;