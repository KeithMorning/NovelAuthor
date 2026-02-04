import React from 'react';
import {
  Box,
  Heading,
  Text,
  Badge,
  Progress,
  HStack,
  VStack,
  Button,
  useColorModeValue,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  IconButton,
  Icon,
} from '@chakra-ui/react';
import { AddIcon, DeleteIcon, EditIcon, HamburgerIcon } from '@chakra-ui/icons';
import { NovelSummary } from '../types';

interface NovelCardProps {
  novel: NovelSummary;
  onView: (id: string) => void;
  onDelete?: (id: string) => void;
}

export const NovelCard: React.FC<NovelCardProps> = ({ novel, onView, onDelete }) => {
  const bg = useColorModeValue('white', 'gray.800');

  const progress = novel.total_chapters > 0
    ? (novel.completed_chapters / novel.total_chapters) * 100
    : 0;

  const statusColor =
    novel.status === '已完成' ? 'green' :
      novel.status === '进行中' ? 'brand' : 'gray';

  return (
    <Box
      bg={bg}
      p={6}
      borderRadius="2xl"
      position="relative"
      transition="all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)"
      _hover={{
        transform: 'translateY(-8px)',
        boxShadow: '2xl',
      }}
      boxShadow="lg"
      border="1px solid"
      borderColor={useColorModeValue('gray.100', 'whiteAlpha.100')}
    >
      <VStack align="stretch" spacing={5}>
        <HStack justify="space-between" align="start">
          <VStack align="start" spacing={1}>
            <Heading size="md" fontFamily="heading" fontWeight="700">
              {novel.title}
            </Heading>
            <Text fontSize="sm" color="gray.500">
              Updated {new Date(novel.updated_at || novel.created_at).toLocaleDateString()}
            </Text>
          </VStack>

          <Menu>
            <MenuButton
              as={IconButton}
              aria-label="Options"
              icon={<HamburgerIcon />}
              variant="ghost"
              size="sm"
            />
            <MenuList>
              <MenuItem icon={<EditIcon />} onClick={() => onView(novel.id)}>
                Resume
              </MenuItem>
              <MenuItem icon={<DeleteIcon />} color="red.500" onClick={() => onDelete && onDelete(novel.id)}>
                Delete
              </MenuItem>
            </MenuList>
          </Menu>
        </HStack>

        <HStack spacing={2}>
          <Badge colorScheme={statusColor} variant="subtle" borderRadius="full" px={2}>
            {novel.status}
          </Badge>
          <Badge variant="outline" borderRadius="full" px={2}>
            {novel.genre}
          </Badge>
        </HStack>

        <Box py={2}>
          <HStack justify="space-between" mb={2}>
            <Text fontSize="xs" fontWeight="bold" color="gray.400" textTransform="uppercase" letterSpacing="wider">
              Progress
            </Text>
            <Text fontSize="xs" fontWeight="bold">
              {novel.completed_chapters} / {novel.total_chapters} Ch
            </Text>
          </HStack>
          <Progress
            value={progress}
            size="xs"
            colorScheme={statusColor}
            borderRadius="full"
            bg={useColorModeValue('gray.100', 'whiteAlpha.200')}
          />
        </Box>

        <Button
          onClick={() => onView(novel.id)}
          colorScheme="brand"
          variant="solid"
          w="full"
          size="md"
          h={12}
          rightIcon={<Icon as={EditIcon} />}
        >
          Continue Writing
        </Button>
      </VStack>
    </Box>
  );
};
