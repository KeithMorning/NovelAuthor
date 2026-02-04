import React, { useState } from 'react';
import {
  Container,
  Heading,
  Button,
  SimpleGrid,
  Text,
  HStack,
  useDisclosure,
  Spinner,
  Center,
  VStack,
  useToast,
  Box,
  Input,
  InputGroup,
  InputLeftElement,
  Icon,
} from '@chakra-ui/react';
import { AddIcon, RepeatIcon, SearchIcon } from '@chakra-ui/icons';
import { useNovels, useDeleteNovel } from '../hooks/useNovels';
import { NovelCard } from '../components/NovelCard';
import { CreateNovelModal } from '../components/CreateNovelModal';
import { ProgressMonitor } from '../components/ProgressMonitor';
import { useNavigate } from 'react-router-dom';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const toast = useToast();
  const { data: novels, isLoading, refetch } = useNovels();
  const deleteNovel = useDeleteNovel();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [searchTerm, setSearchTerm] = useState('');

  // Filter novels
  const filteredNovels = novels?.filter(novel =>
    novel.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    novel.genre.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure? This action cannot be undone.')) {
      try {
        await deleteNovel.mutateAsync(id);
        toast({ title: 'Novel deleted', status: 'success' });
      } catch (error: any) {
        toast({ title: 'Delete failed', status: 'error' });
      }
    }
  };

  return (
    <Box minH="100vh" bg="gray.50">
      <Box bg="white" shadow="sm" borderBottom="1px solid" borderColor="gray.100">
        <Container maxW="container.xl" py={4}>
          <HStack justify="space-between">
            <HStack spacing={4}>
              {/* Logo placeholder */}
              <Box w={8} h={8} bg="brand.500" borderRadius="md" />
              <Heading size="md" letterSpacing="tight">Nover</Heading>
            </HStack>
            <HStack>
              <Button leftIcon={<RepeatIcon />} variant="ghost" onClick={() => refetch()}>
                Refresh
              </Button>
              {/* User Avatar Placeholder */}
              <Box w={8} h={8} bg="gray.200" borderRadius="full" />
            </HStack>
          </HStack>
        </Container>
      </Box>

      <Container maxW="container.xl" py={12}>
        <VStack align="stretch" spacing={10}>

          <HStack justify="space-between" align="center" wrap="wrap" gap={4}>
            <VStack align="start" spacing={1}>
              <Heading size="lg">Your Library</Heading>
              <Text color="gray.500">Manage and write your novels</Text>
            </VStack>

            <HStack>
              <InputGroup w={{ base: 'full', md: '300px' }}>
                <InputLeftElement pointerEvents="none" children={<SearchIcon color="gray.400" />} />
                <Input
                  placeholder="Search novels..."
                  bg="white"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </InputGroup>
              <Button
                leftIcon={<AddIcon />}
                colorScheme="brand"
                size="md"
                px={8}
                onClick={onOpen}
                shadow="lg"
                _hover={{ shadow: 'xl', transform: 'translateY(-2px)' }}
              >
                New Novel
              </Button>
            </HStack>
          </HStack>

          <ProgressMonitor />

          {isLoading ? (
            <Center py={20}>
              <Spinner size="xl" color="brand.500" thickness="3px" />
            </Center>
          ) : filteredNovels && filteredNovels.length > 0 ? (
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={8}>
              {filteredNovels.map((novel) => (
                <NovelCard
                  key={novel.id}
                  novel={novel}
                  onView={(id) => navigate(`/novel/${id}`)}
                  onDelete={handleDelete}
                />
              ))}
            </SimpleGrid>
          ) : (
            <Center py={20} flexDirection="column" gap={6}>
              <Box p={8} bg="white" borderRadius="full" shadow="sm">
                <AddIcon boxSize={12} color="gray.300" />
              </Box>
              <VStack spacing={2}>
                <Text fontSize="xl" fontWeight="bold" color="gray.600">No novels found</Text>
                <Text color="gray.400">Create your first masterpiece today!</Text>
              </VStack>
              <Button colorScheme="brand" onClick={onOpen}>Create Novel</Button>
            </Center>
          )}
        </VStack>

        <CreateNovelModal isOpen={isOpen} onClose={onClose} />
      </Container>
    </Box>
  );
};
