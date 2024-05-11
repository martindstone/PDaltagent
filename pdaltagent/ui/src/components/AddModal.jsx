import {
    useCallback,
    useEffect,
    useState,
    useMemo,
} from 'react';

import {
    Modal,
    ModalOverlay,
    ModalContent,
    ModalHeader,
    ModalFooter,
    ModalBody,
    Input,
    Button,
    Flex,
    FormControl,
    FormLabel,
    Select,
    Text,
    useToast,
} from '@chakra-ui/react';

import ConditionBuilder from './ConditionBuilder';
import DurationInput from './DurationInput';

import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import './DatePickerComponent.scss';

const AddMaintenanceModal = ({ isOpen, onClose, setDataHasChanged }) => {
    const toast = useToast();

    const now = useMemo(() => new Date(), []);
    const inOneHour = useMemo(() => new Date(now.getTime() + 60 * 60 * 1000), [now]);

    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [start, setStart] = useState(now);
    const [end, setEnd] = useState(inOneHour);
    const [condition, setCondition] = useState({});
    const [frequency, setFrequency] = useState('Once');
    const [duration, setDuration] = useState(0);

    const [valid, setValid] = useState(false);
    const [validationHint, setValidationHint] = useState('');

    useEffect(() => {
        // setValid to true if all fields are filled
        if (
            name &&
            start &&
            end &&
            end > start &&
            condition &&
            typeof condition === 'object' &&
            Object.keys(condition).length > 0 &&
            (
                frequency === 'Once' ||
                (
                    frequency === 'Daily' ||
                    frequency === 'Weekly'
                ) && duration > 0 && duration <= (end - start) / 1000
            )
        ) {
            setValid(true);
            setValidationHint('');
        } else {
            setValid(false);
            if (!name) setValidationHint('Name is required');
            else if (!start) setValidationHint('Start time is required');
            else if (!end) setValidationHint('End time is required');
            else if (end <= start) setValidationHint('End time must be after start time');
            else if (!condition || typeof condition !== 'object' || Object.keys(condition).length === 0) setValidationHint('Condition is required');
            else if (frequency !== 'Once' && (!duration || duration <= 0 || duration > (end - start) / 1000)) {
                setValidationHint('Duration is required and must be less than the maintenance window');
            }
        }
    }, [name, start, end, condition, frequency, duration]);

    const clearState = useCallback(() => {
        setName('');
        setDescription('');
        setStart(now);
        setEnd(inOneHour);
        setCondition({});
        setFrequency('Once');
        setDuration(0);
        setValid(false);
        setValidationHint('');
    }, [now, inOneHour]);

    const handleAddMaintenance = useCallback((e) => {
        e.preventDefault();
        const csrfToken = sessionStorage.getItem('csrfToken');
        fetch('/maints', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRF-TOKEN': csrfToken,
            },
            body: JSON.stringify({
                name,
                description,
                start: Math.floor(start.getTime() / 1000),
                end: Math.floor(end.getTime() / 1000),
                condition,
                frequency,
                frequency_data: frequency === 'Once' ? null : {
                    duration,
                },
            })
        })
        .then((res) => res.json())
        .then((data) => {
            if (data?.status === 'ok') {
                onClose();
                clearState();
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
    }, [setDataHasChanged, name, description, start, end, condition, frequency, duration, onClose, toast, clearState]);

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            size="xl"
        >
            <ModalOverlay />
            <ModalContent>
                <ModalHeader>Add Maintenance Window</ModalHeader>
                <form onSubmit={handleAddMaintenance}>
                    <ModalBody>
                        <FormControl>
                            <FormLabel>Name</FormLabel>
                            <Input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} isInvalid={!name} />
                        </FormControl>
                        <FormControl>
                            <FormLabel>Description</FormLabel>
                            <Input placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
                        </FormControl>
                        <Flex direction="row" justify="space-between" align="center" wrap="wrap" gap="20px">
                            <FormControl flex="1">
                                <FormLabel>Start</FormLabel>
                                <DatePicker
                                    id="since-date-input"
                                    className="date-picker"
                                    dateFormat="Pp"
                                    timeCaption="Time"
                                    todayButton="Today"
                                    selectsStart
                                    showTimeSelect
                                    onChange={(date) => {
                                        setStart(date);
                                    }}
                                    selected={start}
                                    maxDate={end}
                                />
                            </FormControl>
                            <FormControl flex="1">
                                <FormLabel>End</FormLabel>
                                <DatePicker
                                    id="since-date-input"
                                    className="date-picker"
                                    dateFormat="Pp"
                                    timeCaption="Time"
                                    todayButton="Today"
                                    selectsStart
                                    showTimeSelect
                                    onChange={(date) => {
                                        setEnd(date);
                                    }}
                                    selected={end}
                                    minDate={start}
                                />
                            </FormControl>
                        </Flex>
                        <FormControl>
                            <FormLabel>Condition</FormLabel>
                            <ConditionBuilder condition={condition} setCondition={setCondition} />
                            {/* <Input placeholder="Condition" value={condition} onChange={(e) => setCondition(e.target.value)} /> */}
                        </FormControl>
                        <FormControl>
                            <FormLabel>Frequency</FormLabel>
                            <Select value={frequency} onChange={(e) => setFrequency(e.target.value)}>
                                <option value="Once">Once</option>
                                <option value="Daily">Daily</option>
                                <option value="Weekly">Weekly</option>
                            </Select>
                        </FormControl>
                        {['Daily', 'Weekly'].includes(frequency) && (
                            <FormControl>
                                <FormLabel>Duration</FormLabel>
                                {/* <Input placeholder="Duration" value={duration} onChange={(e) => setDuration(e.target.value)} /> */}
                                <DurationInput onChange={(durationSeconds) => setDuration(durationSeconds)}/>
                            </FormControl>
                        )}
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
                            Add Maintenance
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

export default AddMaintenanceModal;
