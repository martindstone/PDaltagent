import { useCallback, useEffect, useMemo, useState } from 'react'

import {
  Box,
  Button,
  Flex,
  Text,
  useDisclosure,
  useToast,
} from '@chakra-ui/react';

import LoginModal from './components/LoginModal';
import LogoutButton from './components/LogoutButton';
import TopMenu from './components/TopMenu';

import MyTable from './components/MyTable';
import MaintenanceModal from './components/MaintenanceModal';

import UserModal from './components/users/UserModal';

import {
  addMaint,
} from './util/fetches';

import {
  urlFor,
} from './util/helpers';

function App() {
  const toast = useToast();

  const [needsRefresh, setNeedsRefresh] = useState(true);
  const [needsReload, setNeedsReload] = useState(false);
  const [isReloading, setIsReloading] = useState(false);
  const [dataHasChanged, setDataHasChanged] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loggedInUser, setLoggedInUser] = useState(null);
  const { isOpen, onOpen, onClose } = useDisclosure();

  const { isOpen: isAddOpen, onOpen: onAddOpen, onClose: onAddClose } = useDisclosure();
  const { isOpen: isUserModalOpen, onOpen: onUserModalOpen, onClose: onUserModalClose } = useDisclosure();

  const [maints, setMaints] = useState([]);

  useEffect(() => {
    fetch('/users/me', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
      })
      .then((res) => {
        if (res.ok) {
          setIsLoggedIn(true);
          res.json().then((data) => {
            setLoggedInUser(data);
          });
        } else {
          onOpen();
        }
      }
    );
  }, [isOpen, onOpen, setIsLoggedIn]);

  const isAdmin = useMemo(() => {
    return loggedInUser?.roles?.includes('admin');
  }, [loggedInUser]);

  useEffect(() => {
    if (dataHasChanged) {
      setNeedsReload(true);
    }
  }, [dataHasChanged]);

  useEffect(() => {
    if (isLoggedIn) {
      fetch(urlFor('/login'), {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
      })
      .then((res) => res.json())
      .then((data) => {
        const csrfToken = data?.response?.csrf_token;
        if (csrfToken) {
          sessionStorage.setItem('csrfToken', csrfToken);
        }
      })
      .catch((error) => {
        console.error('Error:', error);
      });
    }
  }, [isLoggedIn]);

  // get maints
  useEffect(() => {
    console.log('useEffect', needsRefresh, isLoggedIn, dataHasChanged)
    if (!needsRefresh && !dataHasChanged) {
      return;
    }
    if (!isLoggedIn) {
      setMaints([]);
      return;
    }
    console.log('Fetching maintenance windows')
    fetch(urlFor('/maints'), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    })
    .then((res) => res.json())
    .then((data) => {
      setMaints(data);
    })
    .catch((error) => {
      console.error('Error:', error);
      toast({
        title: 'Failed to fetch maintenance windows',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    })
    .finally(() => {
      setNeedsRefresh(false);
      setDataHasChanged(false);
    });
  }, [toast, isLoggedIn, needsRefresh, dataHasChanged, setMaints]);

  const reloadServices = useCallback(() => {
    setIsReloading(true);
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
      } else {
          toast({
              title: 'Failed to restart services',
              status: 'error',
              duration: 3000,
              isClosable: true,
          });
        }
    })
    .catch((error) => {
        toast({
            title: 'Failed to restart services',
            description: error,
            status: 'error',
            duration: 3000,
            isClosable: true,
        });
    })
    .finally(() => {
      setNeedsReload(false);
      setIsReloading(false);
      setDataHasChanged(false);
    });
  }, [toast]);

  const handleAddMaint = (maint) => {
    addMaint(maint)
    .then((data) => {
      if (data?.status === 'ok') {
        onAddClose();
        toast({
          title: 'Maintenance window added',
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
        setDataHasChanged(true);
      } else {
        toast({
          title: 'Failed to add maintenance window',
          status: 'error',
          duration: 3000,
          isClosable: true,
        });
      }
    })
    .catch((error) => {
      console.error('Error:', error);
      toast({
        title: 'Failed to add maintenance window',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    });
  }

  return (
    <Box position="fixed" top={0} left={0} right={0} bottom={0} overflow="hidden">
      <LoginModal isOpen={isOpen} onClose={onClose} />
      <MaintenanceModal isOpen={isAddOpen} onClose={onAddClose} onSubmit={handleAddMaint} />
      <UserModal isOpen={isUserModalOpen} onOpen={onUserModalOpen} onClose={onUserModalClose} isAdmin={isAdmin} />
      {isLoggedIn && (
        <>
          <Box as="header" top={0} h="60px" w="100%" borderBottom="1px solid black">
            <Flex justifyContent="space-between" alignItems="center" h="100%" px={4}>
              <Box>
                <Button colorScheme="blue" onClick={onAddOpen}>Add</Button>
              </Box>
              <Text fontSize="xl" fontWeight="bold">Maintenance Windows</Text>
              <Box>
                {needsReload && (
                  <>
                    <Text display="inline" fontSize="sm" fontStyle="italic" mr={1}>Configuration modified</Text>
                    <Button
                      colorScheme="blue"
                      onClick={() => reloadServices()}
                      isDisabled={isReloading}
                    >
                      {isReloading ? 'Restarting...' : 'Restart PDaltagent'}
                    </Button>
                  </>
                )}
                <TopMenu
                  toast={toast}
                  setNeedsRefresh={setNeedsRefresh}
                  openAddUserModal={onUserModalOpen}
                />
              </Box>
            </Flex>
          </Box>
          <Box as="main" overflowY="scroll" height="calc(100vh - 60px)">
            {maints.length === 0 && (
              <p>No maints found</p>
            )}
            {maints.length > 0 && (
              <MyTable data={maints} setDataHasChanged={setDataHasChanged} />
            )}
          </Box>
          <LogoutButton />
        </>
      )}
    </Box>
  )
}

export default App
