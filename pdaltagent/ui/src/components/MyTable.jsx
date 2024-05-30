import {
  useState,
  useMemo,
  useCallback,
  useEffect,
} from 'react'

import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'

import {
  Button,
  Code,
  Flex,
  Table,
  Thead,
  Tbody,
  Tr,
  Box,
  Input,
  Popover,
  PopoverArrow,
  PopoverTrigger,
  PopoverContent,
  useDisclosure,
  Tfoot,
  Text,
  Tabs,
  Tab,
  TabList,
  useToast,
} from '@chakra-ui/react';

import Condition from './Condition';
import DeleteModal from './DeleteModal';
import MaintenanceModal from './MaintenanceModal';

import {
  formatLocalShortDate,
  secondsToHuman,
  stringifyExpression,
} from '../util/helpers'

import {
  updateMaint,
} from '../util/fetches';

const Filter = ({
  column,
}) => {
  const columnFilterValue = column.getFilterValue()

  if (column.columnDef.meta?.search === 'text') {
    return (
      <Input
        size="xs"
        type="text"
        value={(columnFilterValue ?? '')}
        onChange={e => column.setFilterValue(e.target.value)}
        placeholder={`Search...`}
      />
    )
  }
  return null
}

const MyTable = ({
  data,
  setDataHasChanged,
}) => {
  const toast = useToast();

  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure();
  const { isOpen: isEditOpen, onOpen: onEditOpen, onClose: onEditClose } = useDisclosure();
  const [currentRecord, setCurrentRecord] = useState(null);
  const [globalFilter, setGlobalFilter] = useState('all');

  const handleDelete = useCallback((row) => {
    if (row.original.id) {
      setCurrentRecord(row.original);
      onDeleteOpen();
    }
  }, [onDeleteOpen]);

  const handleEditMaint = useCallback((row) => {
    if (row.original.id) {
      setCurrentRecord(row.original);
      onEditOpen();
    }
  }, [onEditOpen]);

  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize: 10,
  })

  const columnHelper = createColumnHelper()

  const columns = useMemo(
    () => [
      {
        accessorKey: 'maintenance_key',
        header: 'Maintenance Key',
        cell: info => info.getValue(),
        footer: props => props.column.id,
        meta: {
          width: 20,
          search: 'text',
        }
      },
      {
        accessorKey: 'name',
        header: 'Name',
        cell: info => info.getValue(),
        footer: props => props.column.id,
        meta: {
          search: 'text',
          width: 40,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        },
      },
      {
        accessorKey: 'condition',
        header: 'Condition',
        filterFn: (row, id, filterValue) => {
          const value = row.original[id];
          return stringifyExpression(value).toLowerCase().includes(filterValue.toLowerCase());
        },
        cell: info => (
          <Box>
            <Popover trigger="hover" size="content" preventOverflow>
              <PopoverTrigger>
                <Box overflow="hidden" textOverflow="ellipsis" whiteSpace="nowrap">
                  {stringifyExpression(info.getValue())}
                </Box>
              </PopoverTrigger>
              <PopoverContent p={1} w="content">
                <PopoverArrow />
                <Box p={1} maxW={800}>
                  <Text fontWeight="bold">Text:</Text>
                  <Code m={2} whiteSpace="wrap">
                    {stringifyExpression(info.getValue())}
                  </Code>
                  <Text fontWeight="bold">Parsed:</Text>
                  <Box m={2}>
                    <Condition condition={info.getValue()} />
                  </Box>
                </Box>
              </PopoverContent>
            </Popover>
          </Box>
        ),
        footer: props => props.column.id,
        meta: {
          search: 'text',
          width: 60,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        },
      },
      columnHelper.accessor('start', {
        header: 'Start',
        cell: info => formatLocalShortDate(info.getValue()),
      }),
      columnHelper.accessor('end', {
        header: 'End',
        cell: info => formatLocalShortDate(info.getValue()),
      }),
      columnHelper.accessor('updated_by', {
        header: 'Updated By',
        cell: info => info.getValue(),
      }),
      columnHelper.accessor('updated_at', {
        header: 'Updated At',
        cell: info => formatLocalShortDate(info.getValue()),
      }),
      columnHelper.accessor('frequency', {
        header: 'Frequency',
        cell: info => {
          const f = info.getValue();
          if (['daily', 'weekly'].includes(f.toLowerCase())) {
            const d = info.row.original.frequency_data.duration;
            return `${f} (${secondsToHuman(d)})`;
          } else {
            return f;
          }
        },
      }),
      columnHelper.display({
        id: 'actions',
        header: 'Actions',
        cell: info => (
          <Flex>
            <Button size="sm" ml={1} colorScheme="blue" onClick={() => handleEditMaint(info.row)}>Edit</Button>
            <Button size="sm" ml={1} colorScheme="red" onClick={() => handleDelete(info.row)}>Delete</Button>
          </Flex>
        ),
      }),
    ],
    [columnHelper, handleDelete, handleEditMaint]
  )

  const filteredData = useMemo(() => {
    console.log('filter data', globalFilter);
    // start and end should be integer seconds since epoch
    const now = new Date().getTime() / 1000;
    if (globalFilter === 'active') {
      return data.filter(row => row.end > now);
    }
    if (globalFilter === 'inactive') {
      return data.filter(row => row.end <= now);
    }
    return data;
  }, [data, globalFilter]);

  const table = useReactTable({
    columns,
    data: filteredData,
    // debugTable: true,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onPaginationChange: setPagination,
    state: {
      pagination,
    },
    initialState: {
      sorting: [
        {
          id: 'updated_at',
          desc: true,
        }
      ]
    },
  })

  const tabValues = useMemo(() => ([
    { value: 'all', label: 'All' },
    { value: 'active', label: 'Active' },
    { value: 'inactive', label: 'Inactive' },
  ]), []);

  const [selectedTabIndex, setSelectedTabIndex] = useState(0);

  useEffect(() => {
    setGlobalFilter(tabValues[selectedTabIndex].value);
  }, [selectedTabIndex, tabValues]);

  const handleEditSubmit = (maint) => {
    const id = currentRecord.id;
    updateMaint(id, maint)
    .then((data) => {
      if (data?.status === 'ok') {
        onEditClose();
        toast({
          title: 'Maintenance window saved',
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
        setDataHasChanged(true);
      } else {
        toast({
          title: 'Failed to save maintenance window',
          status: 'error',
          duration: 3000,
          isClosable: true,
        });
      }
    })
    .catch((error) => {
      console.error('Error:', error);
      toast({
        title: 'Failed to save maintenance window',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    });
  }

  return (
    <Box p={2}>
      <DeleteModal isOpen={isDeleteOpen} onClose={onDeleteClose} record={currentRecord} setDataHasChanged={setDataHasChanged} />
      <MaintenanceModal isOpen={isEditOpen} onClose={onEditClose} record={currentRecord} onSubmit={handleEditSubmit} />
      <div className="h-2" />
      <Tabs onChange={(index) => setSelectedTabIndex(index)} mb={2}>
        <TabList>
          {tabValues.map((tab, index) => (
            <Tab key={tab.value} isSelected={selectedTabIndex === index}>
              {tab.label}
            </Tab>
          ))}
        </TabList>
      </Tabs>
      <Table variant="striped">
        <Thead>
          {table.getHeaderGroups().map(headerGroup => (
            <Tr key={headerGroup.id}>
              {headerGroup.headers.map(header => {
                return (
                  <Box as="th" key={header.id} colSpan={header.colSpan}>
                    <Box
                      {...{
                        className: header.column.getCanSort()
                          ? 'cursor-pointer select-none'
                          : '',
                        onClick: header.column.getToggleSortingHandler(),
                      }}
                    >
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                      {{
                        asc: ' 🔼',
                        desc: ' 🔽',
                      }[header.column.getIsSorted()] ?? null}
                    </Box>
                    {header.column.getCanFilter() ? (
                      <Box>
                        <Filter column={header.column} table={table} />
                      </Box>
                    ) : null}
                  </Box>
                )
              })}
            </Tr>
          ))}
        </Thead>
        <Tbody>
          {table.getRowModel().rows.map(row => {
            return (
              <Box as="tr" py={1} key={row.id}>
                {row.getVisibleCells().map(cell => {
                  return (
                    <Box
                      as="td"
                      p={1}
                      maxW={cell.column.columnDef?.meta?.width || null}
                      overflow={cell.column.columnDef?.meta?.overflow || null}
                      textOverflow={cell.column.columnDef?.meta?.textOverflow || null}
                      whiteSpace={cell.column.columnDef?.meta?.whiteSpace || null}
                      key={cell.id}
                      fontSize="sm"
                    >
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </Box>
                  )
                })}
              </Box>
            )
          })}
        </Tbody>
        <Tfoot>
          <Box as="tr">
            <Box as="td" colSpan={columns.length}>
              <Flex mt={4} borderTop="1px solid black" justifyContent="space-between" alignItems="center" px={4}>
                <Box>
                  <Button
                    mx={1}
                    p={1}
                    onClick={() => table.firstPage()}
                    isDisabled={!table.getCanPreviousPage()}
                  >
                    {'<<'}
                  </Button>
                  <Button
                    mx={1}
                    p={1}
                    onClick={() => table.previousPage()}
                    isDisabled={!table.getCanPreviousPage()}
                  >
                    {'<'}
                  </Button>
                </Box>
                <Box>
                  <Text align="center">
                    Page {' '}
                    {table.getState().pagination.pageIndex + 1} of {' '}
                    {table.getPageCount().toLocaleString()}
                  </Text>
                  <Text align="center">
                    Showing {table.getRowModel().rows.length.toLocaleString()} of{' '}
                    {table.getRowCount().toLocaleString()} rows
                  </Text>
                </Box>
                <Box>
                  <Button
                    mx={1}
                    p={1}
                    onClick={() => table.nextPage()}
                    isDisabled={!table.getCanNextPage()}
                  >
                    {'>'}
                  </Button>
                  <Button
                    mx={1}
                    p={1}
                    onClick={() => table.lastPage()}
                    isDisabled={!table.getCanNextPage()}
                  >
                    {'>>'}
                  </Button>
                </Box>
              </Flex>
            </Box>
          </Box>
        </Tfoot>
      </Table>
    </Box>
  )
}

export default MyTable;