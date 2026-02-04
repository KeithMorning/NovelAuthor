import React, { useState } from 'react';
import {
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Badge,
  Box,
  Button,
  SimpleGrid,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Spinner,
  Center,
  useToast,
  useColorModeValue,
  Icon,
  useDisclosure,
  Divider,
} from '@chakra-ui/react';
import { ArrowBackIcon, AddIcon, DownloadIcon, TimeIcon } from '@chakra-ui/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { useNovel, useWriteChapter } from '../hooks/useNovels';
import { ProgressMonitor } from '../components/ProgressMonitor';
import { ExportModal } from '../components/ExportModal';

export const NovelDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const { data: novel, isLoading } = useNovel(id!);
  const writeChapter = useWriteChapter();
  const { isOpen: isExportOpen, onOpen: onExportOpen, onClose: onExportClose } = useDisclosure();

  const handleWriteChapter = async (chapterNumber: number) => {
    try {
      await writeChapter.mutateAsync({ novelId: id!, chapterNumber });
      toast({
        title: 'Started writing',
        description: `Chapter ${chapterNumber} is being generated...`,
        status: 'info',
      });
    } catch (error: any) {
      toast({
        title: 'Failed to start',
        description: error.response?.data?.error || 'Please try again',
        status: 'error',
      });
    }
  };

  const bg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.100', 'whiteAlpha.100');

  if (isLoading) {
    return (
      <Center h="100vh">
        <Spinner size="xl" color="brand.500" thickness="3px" />
      </Center>
    );
  }

  if (!novel) {
    return (
      <Container centerContent py={20}>
        <Text fontSize="xl">Novel not found</Text>
        <Button mt={4} onClick={() => navigate('/')}>Back Home</Button>
      </Container>
    );
  }

  return (
    <Box minH="100vh" bg="gray.50">
      <Box bg="white" borderBottom="1px solid" borderColor="gray.100" py={4}>
        <Container maxW="container.xl">
          <Button
            leftIcon={<ArrowBackIcon />}
            variant="ghost"
            size="sm"
            mb={2}
            onClick={() => navigate('/')}
          >
            Back to Library
          </Button>
          <HStack justify="space-between" align="start">
            <VStack align="start" spacing={1}>
              <Heading size="xl" fontFamily="heading">{novel.title}</Heading>
              <HStack>
                <Badge colorScheme="brand" variant="solid" borderRadius="full" px={3}>{novel.status}</Badge>
                <Badge variant="outline" borderRadius="full" px={3}>{novel.genre}</Badge>
                <Badge colorScheme="purple" variant="subtle" borderRadius="full" px={3}>{novel.style}</Badge>
              </HStack>
            </VStack>
            <Button leftIcon={<DownloadIcon />} variant="outline" onClick={onExportOpen}>
              Export
            </Button>
          </HStack>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        <VStack align="stretch" spacing={6}>
          {/* Theme/Summary Card */}
          {novel.theme && (
            <Box bg={bg} p={6} borderRadius="xl" shadow="sm" border="1px solid" borderColor={borderColor}>
              <Text fontWeight="bold" fontSize="sm" color="gray.500" textTransform="uppercase" letterSpacing="wider" mb={2}>
                Theme & Premise
              </Text>
              <Text fontSize="lg" lineHeight="tall">{novel.theme}</Text>
            </Box>
          )}

          <ProgressMonitor novelId={id} />

          <Box bg={bg} borderRadius="xl" shadow="sm" border="1px solid" borderColor={borderColor} overflow="hidden">
            <Tabs colorScheme="brand" size="lg">
              <TabList px={4} pt={2}>
                <Tab fontWeight="600">Chapters</Tab>
                <Tab fontWeight="600">Characters</Tab>
                <Tab fontWeight="600">Plot Points</Tab>
              </TabList>

              <TabPanels>
                {/* Chapters Tab */}
                <TabPanel p={6}>
                  <VStack align="stretch" spacing={4}>
                    <HStack justify="space-between">
                      <Text fontWeight="bold" fontSize="lg">
                        {novel.chapters?.length || 0} / {novel.total_chapters} Chapters
                      </Text>
                      <Button
                        leftIcon={<AddIcon />}
                        size="sm"
                        colorScheme="brand"
                        onClick={() => handleWriteChapter((novel.chapters?.length || 0) + 1)}
                        isLoading={writeChapter.isPending}
                      >
                        Write Next Chapter
                      </Button>
                    </HStack>

                    {novel.chapters && novel.chapters.length > 0 ? (
                      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
                        {novel.chapters.map((chapter) => (
                          <Box
                            key={chapter.number}
                            p={5}
                            borderRadius="lg"
                            border="1px solid"
                            borderColor={borderColor}
                            _hover={{ borderColor: 'brand.200', bg: 'brand.50' }}
                            transition="all 0.2s"
                            cursor="pointer"
                            onClick={() => navigate(`/novel/${id}/chapter/${chapter.number}`)}
                          >
                            <HStack justify="space-between" mb={2}>
                              <HStack>
                                <Badge colorScheme="brand" borderRadius="full" px={2}>CH {chapter.number}</Badge>
                                <Text fontWeight="bold">{chapter.title}</Text>
                              </HStack>
                              <Badge textTransform="capitalize" variant="subtle">{chapter.status}</Badge>
                            </HStack>
                            <Text fontSize="sm" color="gray.600" noOfLines={2} mb={3}>
                              {chapter.summary || 'No summary available.'}
                            </Text>
                            <HStack fontSize="xs" color="gray.400">
                              <Icon as={TimeIcon} />
                              <Text>{chapter.word_count || 0} words</Text>
                            </HStack>
                          </Box>
                        ))}
                      </SimpleGrid>
                    ) : (
                      <Center py={12} bg="gray.50" borderRadius="lg" flexDirection="column" gap={4}>
                        <Text color="gray.500">No chapters written yet.</Text>
                        <Button colorScheme="brand" onClick={() => handleWriteChapter(1)}>Start Writing</Button>
                      </Center>
                    )}
                  </VStack>
                </TabPanel>

                {/* Characters Tab */}
                <TabPanel p={6}>
                  <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
                    {novel.characters?.map((char, index) => (
                      <Box key={index} p={5} borderRadius="lg" bg="gray.50" border="1px solid" borderColor={borderColor}>
                        <HStack justify="space-between" mb={3}>
                          <Text fontWeight="bold" fontSize="lg">{char.name}</Text>
                          <Badge colorScheme="purple">{char.role}</Badge>
                        </HStack>
                        <VStack align="start" spacing={1}>
                          <Text fontSize="xs" fontWeight="bold" color="gray.500" textTransform="uppercase">Personality</Text>
                          <Text fontSize="sm" mb={2}>{char.personality}</Text>
                          <Text fontSize="xs" fontWeight="bold" color="gray.500" textTransform="uppercase">Background</Text>
                          <Text fontSize="sm" color="gray.600" noOfLines={3}>{char.background}</Text>
                        </VStack>
                      </Box>
                    ))}
                  </SimpleGrid>
                </TabPanel>

                {/* Plot Points Tab */}
                <TabPanel p={6}>
                  <VStack align="stretch" spacing={4}>
                    {novel.plot_points?.map((plot, index) => (
                      <Box key={index} p={4} borderRadius="lg" borderLeft="4px solid" borderColor="brand.400" bg="gray.50">
                        <HStack justify="space-between" mb={1}>
                          <Text fontWeight="bold">{plot.name}</Text>
                          <Badge colorScheme={plot.importance === '高' ? 'red' : 'gray'}>
                            {plot.importance} Priority
                          </Badge>
                        </HStack>
                        <Text fontSize="sm" color="gray.700" mb={1}>{plot.description}</Text>
                        <Text fontSize="xs" color="gray.500">Target: {plot.chapter_range}</Text>
                      </Box>
                    ))}
                  </VStack>
                </TabPanel>
              </TabPanels>
            </Tabs>
          </Box>
        </VStack>
      </Container>

      <ExportModal isOpen={isExportOpen} onClose={onExportClose} novel={novel} />
    </Box>
  );
};
