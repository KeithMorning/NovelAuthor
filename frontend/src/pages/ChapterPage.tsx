import React, { useState } from 'react';
import {
  Container,
  Button,
  HStack,
  VStack,
  Box,
  useToast,
  useDisclosure,
  Text,
  Badge,
  Spinner,
  Center,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Select,
  FormControl,
  FormLabel,
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  useColorModeValue,
} from '@chakra-ui/react';
import { ArrowBackIcon } from '@chakra-ui/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { useNovel } from '../hooks/useNovels';
import { ChapterEditor } from '../components/ChapterEditor';
import { chaptersApi } from '../api/novels';
import { ChapterContent } from '../types';

export const ChapterPage: React.FC = () => {
  const { novelId, chapterNumber } = useParams<{ novelId: string; chapterNumber: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const { data: novel, isLoading } = useNovel(novelId!);

  const [chapterContent, setChapterContent] = useState<ChapterContent | null>(null);
  const [isLoadingChapter, setIsLoadingChapter] = useState(true);
  const [isPolishing, setIsPolishing] = useState(false);
  const [isReviewing, setIsReviewing] = useState(false);
  const [polishIntensity, setPolishIntensity] = useState<'low' | 'medium' | 'high'>('medium');
  const [polishedContent, setPolishedContent] = useState<string | null>(null);
  const [reviewResult, setReviewResult] = useState<any>(null);

  const { isOpen: isPolishModalOpen, onOpen: onPolishModalOpen, onClose: onPolishModalClose } = useDisclosure();
  const { isOpen: isReviewModalOpen, onOpen: onReviewModalOpen, onClose: onReviewModalClose } = useDisclosure();

  const chapterNum = parseInt(chapterNumber!);
  const chapter = novel?.chapters?.find(ch => ch.number === chapterNum);

  React.useEffect(() => {
    const loadChapter = async () => {
      if (!novelId || !chapterNum) return;
      setIsLoadingChapter(true);
      try {
        const content = await chaptersApi.getChapter(novelId, chapterNum);
        setChapterContent(content);
      } catch (error) {
        toast({ title: 'Failed to load chapter', status: 'error' });
      } finally {
        setIsLoadingChapter(false);
      }
    };
    loadChapter();
  }, [novelId, chapterNum, toast]);

  const handleSave = async (content: string) => {
    // Mock save for now, assume API hook later
    await new Promise(resolve => setTimeout(resolve, 500));
  };

  const handlePolish = async () => {
    setIsPolishing(true);
    try {
      await chaptersApi.polishChapter(novelId!, chapterNum, polishIntensity);
      onPolishModalClose();
      toast({
        title: 'Polishing started',
        description: 'Check progress via WebSocket',
        status: 'info',
      });
    } catch (error: any) {
      toast({ title: 'Polish failed', description: error.message, status: 'error' });
    } finally {
      setIsPolishing(false);
    }
  };

  const handleReview = async () => {
    setIsReviewing(true);
    try {
      const result = await chaptersApi.reviewChapter(novelId!, chapterNum);
      setReviewResult(result);
      onReviewModalOpen();
    } catch (error: any) {
      toast({ title: 'Review failed', description: error.message, status: 'error' });
    } finally {
      setIsReviewing(false);
    }
  };

  const applyPolish = () => {
    if (polishedContent && chapterContent) {
      setChapterContent({ ...chapterContent, content: polishedContent });
      setPolishedContent(null);
      toast({ title: 'Polish applied', status: 'success' });
    }
  };

  if (isLoading || isLoadingChapter) {
    return (
      <Center h="100vh">
        <Spinner size="xl" color="brand.500" thickness="3px" />
      </Center>
    );
  }

  if (!novel || !chapter || !chapterContent) {
    return (
      <Container centerContent py={20}>
        <Text fontSize="xl">Chapter not found</Text>
        <Button mt={4} onClick={() => navigate(`/novel/${novelId}`)}>Go Back</Button>
      </Container>
    );
  }

  return (
    <Box h="100vh" display="flex" flexDirection="column" bg="gray.50">
      <Container maxW="container.xl" h="full" py={4} display="flex" flexDirection="column">
        {/* Header */}
        <HStack mb={4} justify="space-between">
          <Button
            leftIcon={<ArrowBackIcon />}
            variant="ghost"
            onClick={() => navigate(`/novel/${novelId}`)}
          >
            Back to Novel
          </Button>

          <HStack spacing={3}>
            <Button
              colorScheme="accent"
              variant="outline"
              onClick={onPolishModalOpen}
              isLoading={isPolishing}
            >
              Polish
            </Button>
            <Button
              colorScheme="brand"
              onClick={handleReview}
              isLoading={isReviewing}
            >
              Review
            </Button>
          </HStack>
        </HStack>

        {/* Main Content */}
        <Box flex="1" overflow="hidden">
          {polishedContent ? (
            <Tabs h="full" variant="enclosed" colorScheme="brand">
              <TabList>
                <Tab>Original</Tab>
                <Tab>Polished Version</Tab>
              </TabList>
              <TabPanels h="full">
                <TabPanel h="full" p={0} pt={2}>
                  <ChapterEditor
                    novelId={novelId!}
                    chapterNumber={chapterNum}
                    initialContent={chapterContent.content}
                    readOnly
                  />
                </TabPanel>
                <TabPanel h="full" p={0} pt={2} display="flex" flexDirection="column">
                  <HStack justify="flex-end" mb={2}>
                    <Button size="sm" onClick={() => setPolishedContent(null)}>Discard</Button>
                    <Button size="sm" colorScheme="brand" onClick={applyPolish}>Apply Changes</Button>
                  </HStack>
                  <Box flex={1}>
                    <ChapterEditor
                      novelId={novelId!}
                      chapterNumber={chapterNum}
                      initialContent={polishedContent}
                      readOnly
                    />
                  </Box>
                </TabPanel>
              </TabPanels>
            </Tabs>
          ) : (
            <ChapterEditor
              novelId={novelId!}
              chapterNumber={chapterNum}
              initialContent={chapterContent.content}
              initialTitle={chapterContent.title}
              onSave={handleSave}
            />
          )}
        </Box>
      </Container>

      {/* Modals */}
      <Modal isOpen={isPolishModalOpen} onClose={onPolishModalClose} isCentered>
        <ModalOverlay backdropFilter="blur(5px)" />
        <ModalContent>
          <ModalHeader>Polish Chapter</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <FormControl>
              <FormLabel>Intensity</FormLabel>
              <Select value={polishIntensity} onChange={(e: any) => setPolishIntensity(e.target.value)}>
                <option value="low">Low - Fix basics</option>
                <option value="medium">Medium - Improve flow</option>
                <option value="high">High - Creative rewrite</option>
              </Select>
            </FormControl>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onPolishModalClose}>Cancel</Button>
            <Button colorScheme="brand" onClick={handlePolish} isLoading={isPolishing}>Start Polishing</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      <Modal isOpen={isReviewModalOpen} onClose={onReviewModalClose} size="xl" scrollBehavior="inside">
        <ModalOverlay backdropFilter="blur(5px)" />
        <ModalContent>
          <ModalHeader>Review Report</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {reviewResult && (
              <VStack align="stretch" spacing={6}>
                <Box p={4} bg="brand.50" borderRadius="lg">
                  <Text fontWeight="bold" mb={2}>Overall Score</Text>
                  <Text fontSize="4xl" fontWeight="800" color="brand.600">{reviewResult.overall_score}/100</Text>
                </Box>

                {/* Add more review content rendering here similar to original but styled better */}
                <Text>{reviewResult.comment}</Text>
              </VStack>
            )}
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
};
