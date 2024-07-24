import {
  useCallback,
  useEffect,
  useState,
  useMemo,
} from 'react';

import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import './DatePickerComponent.scss';

import {
  Box,
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
} from '@chakra-ui/react';

import ConditionEditor from './bpql/ConditionEditor';
import FrequencyDescription from './bpql/FrequencyDescription';
import DurationInput from './DurationInput';

const MaintenanceModal = ({ isOpen, onClose, record, onSubmit }) => {
  const defaultStart = useMemo(() => {
    const start = new Date();
    start.setHours(start.getHours() + 1);
    start.setMinutes(0);
    start.setSeconds(0);
    start.setMilliseconds(0);
    return start;
  }, []);

  const defaultEnd = useMemo(() => {
    const end = new Date(defaultStart);
    end.setHours(end.getHours() + 1);
    return end;
  }, [defaultStart]);

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [start, setStart] = useState(defaultStart);
  const [end, setEnd] = useState(defaultEnd);
  const [frequency, setFrequency] = useState('Once');
  const [duration, setDuration] = useState(0);
  const [condition, setCondition] = useState({ "=": ["hostname", "localhost"] });
  const [valid, setValid] = useState(false);
  const [conditionIsValid, setConditionIsValid] = useState(false);
  const [validationHint, setValidationHint] = useState('');

  useEffect(() => {
      if (record) {
          setName(record.name || '');
          setDescription(record.description || '');
          setStart(record.start ? new Date(record.start * 1000) : defaultStart);
          setEnd(record.end ? new Date(record.end * 1000) : defaultEnd);
          setFrequency(record.frequency || 'Once');
          setDuration(record.frequency_data?.duration || 0);
          setCondition(record.condition || { "=": ["hostname", "localhost"] });
      }
  }, [record, defaultStart, defaultEnd]);

  useEffect(() => {
      // setValid to true if all fields are filled
      if (
          name &&
          start &&
          end &&
          end > start &&
          condition &&
          conditionIsValid &&
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
  }, [name, start, end, condition, frequency, duration, conditionIsValid]);

  const handleFrequencyChange = useCallback((e) => {
      if (frequency === 'Once') {
          setDuration(3600);
      }
      if (e.target.value === 'Once') {
          setDuration(0);
      }
      setFrequency(e.target.value);
  }, [frequency]);

  const handleStartChange = useCallback((date) => {
      setStart(date);
      if (date >= end) {
        const newStart = new Date(date);
        newStart.setHours(newStart.getHours() + 1);
        setEnd(newStart);
      }
  }, [end]);

  const handleSubmit = useCallback((e) => {
      e.preventDefault();
      const maint = {
          name,
          description,
          start: Math.floor(start.getTime() / 1000),
          end: Math.floor(end.getTime() / 1000),
          condition,
          frequency,
          frequency_data: frequency === 'Once' ? null : {
              duration,
          },
      };
      onSubmit(maint);
      onClose();
  }, [name, description, start, end, condition, frequency, duration, onClose, onSubmit]);

  return (
      <Modal isOpen={isOpen} onClose={onClose} size="xxl">
          <ModalOverlay />
          <form onSubmit={handleSubmit}>
              <ModalContent>
                  <ModalHeader>
                      {record?.maintenance_key ? `Edit Maintenance Window ${record.maintenance_key}` : 'Add Maintenance Window'}
                  </ModalHeader>
                  <ModalBody>
                      <Flex direction="row" justify="space-between" align="center" wrap="wrap" gap="20px">
                          <FormControl flex="1">
                              <FormLabel>Name</FormLabel>
                              <Input size="sm" placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} isInvalid={!name} />
                          </FormControl>
                          <FormControl flex="1">
                              <FormLabel>Description</FormLabel>
                              <Input size="sm" placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
                          </FormControl>
                      </Flex>
                      <FormControl mt={2}>
                          <FormLabel>Condition</FormLabel>
                          <Box h="40vh">
                              <ConditionEditor
                                condition={condition}
                                setCondition={setCondition}
                                setIsValid={setConditionIsValid}
                                initialMode="plaintext"
                              />
                          </Box>
                      </FormControl>
                      <Box borderWidth="1px" borderRadius="md" p={2} mt={2}>
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
                                  onChange={handleStartChange}
                                  selected={start}
                                  // maxDate={end}
                              />
                          </FormControl>
                          <FormControl flex="1">
                              <FormLabel>End</FormLabel>
                              <DatePicker
                                  id="until-date-input"
                                  className="date-picker"
                                  dateFormat="Pp"
                                  timeCaption="Time"
                                  todayButton="Today"
                                  selectsStart
                                  showTimeSelect
                                  onChange={(date) => setEnd(date)}
                                  selected={end}
                                  minDate={start}
                              />
                          </FormControl>
                          <FormControl flex="1">
                              <FormLabel>Repeat</FormLabel>
                              <Select size="sm" value={frequency} onChange={handleFrequencyChange}>
                                  <option value="Once">None</option>
                                  <option value="Daily">Daily</option>
                                  <option value="Weekly">Weekly</option>
                              </Select>
                          </FormControl>
                          {['Daily', 'Weekly'].includes(frequency) && (
                              <FormControl flex="1">
                                  <FormLabel>Duration</FormLabel>
                                  <DurationInput size="xs" value={duration} onChange={(durationSeconds) => setDuration(durationSeconds)} />
                              </FormControl>
                          )}
                      </Flex>
                        <Flex direction="row" justify="space-between" align="center" wrap="wrap" gap="20px">
                        </Flex>
                        <FrequencyDescription start={start} end={end} frequency={frequency} duration={duration} />
                      </Box>
                      {validationHint && (
                          <Text display="block" color="red" fontSize="sm" fontStyle="italic" my={2}>
                              {validationHint}
                          </Text>
                      )}
                  </ModalBody>
                  <ModalFooter>
                      <Button type="submit" colorScheme="blue" mr={3} isDisabled={!valid}>
                          {record?.maintenance_key ? 'Update' : 'Add'}
                      </Button>
                      <Button onClick={onClose}>
                          Cancel
                      </Button>
                  </ModalFooter>
              </ModalContent>
          </form>
      </Modal>
  );
};

export default MaintenanceModal;
