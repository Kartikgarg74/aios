import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { invoke } from '@tauri-apps/api/tauri';
import { Mail, MessageSquare, Users, Plus } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

type Message = {
  id: string;
  from: string;
  content: string;
  timestamp: string;
  read: boolean;
};

type Contact = {
  id: string;
  name: string;
  email: string;
  lastContact: string;
};

const CommunicationHub: React.FC = () => {
  const [newMessage, setNewMessage] = React.useState('');
  const [activeTab, setActiveTab] = React.useState('messages');
  const [selectedContact, setSelectedContact] = React.useState<string | null>(null);

  const { data: messages } = useQuery({
    queryKey: ['messages'],
    queryFn: () => invoke<Message[]>('get_messages')
  });

  const { data: contacts } = useQuery({
    queryKey: ['contacts'],
    queryFn: () => invoke<Contact[]>('get_contacts')
  });

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedContact) return;
    
    try {
      await invoke('send_message', {
        contactId: selectedContact,
        content: newMessage
      });
      setNewMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-6 w-6" />
            Communication Hub
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="messages">
                <MessageSquare className="h-4 w-4 mr-2" />
                Messages
              </TabsTrigger>
              <TabsTrigger value="email">
                <Mail className="h-4 w-4 mr-2" />
                Email
              </TabsTrigger>
              <TabsTrigger value="contacts">
                <Users className="h-4 w-4 mr-2" />
                Contacts
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="messages">
              <div className="grid grid-cols-3 gap-4">
                <div className="col-span-1 border-r pr-4">
                  <h3 className="font-medium mb-2">Conversations</h3>
                  <div className="space-y-2">
                    {contacts?.map(contact => (
                      <div 
                        key={contact.id}
                        onClick={() => setSelectedContact(contact.id)}
                        className={`p-2 rounded cursor-pointer ${selectedContact === contact.id ? 'bg-secondary' : 'hover:bg-secondary/50'}`}
                      >
                        <div className="font-medium">{contact.name}</div>
                        <div className="text-sm text-gray-500">{contact.email}</div>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="col-span-2 space-y-4">
                  {selectedContact ? (
                    <>
                      <div className="border rounded-lg p-4 h-64 overflow-y-auto space-y-4">
                        {messages
                          ?.filter(msg => msg.from === selectedContact)
                          .map(msg => (
                            <div key={msg.id} className={`p-2 rounded ${msg.read ? '' : 'bg-blue-50'}`}>
                              <div className="text-sm text-gray-500">{new Date(msg.timestamp).toLocaleString()}</div>
                              <div>{msg.content}</div>
                            </div>
                          ))
                        }
                      </div>
                      
                      <div className="flex gap-2">
                        <Input 
                          value={newMessage} 
                          onChange={(e) => setNewMessage(e.target.value)} 
                          placeholder="Type a message..." 
                          className="flex-1" 
                        />
                        <Button onClick={sendMessage}>
                          Send
                        </Button>
                      </div>
                    </>
                  ) : (
                    <div className="text-center text-gray-500 py-16">
                      Select a contact to start chatting
                    </div>
                  )}
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="email">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="font-medium">Inbox</h3>
                  <Button size="sm" variant="outline">
                    <Plus className="h-4 w-4 mr-2" />
                    New Email
                  </Button>
                </div>
                
                <div className="border rounded-lg p-4 h-96 overflow-y-auto">
                  {messages?.map(msg => (
                    <div key={msg.id} className="p-2 border-b last:border-b-0 hover:bg-secondary/50 cursor-pointer">
                      <div className="flex justify-between">
                        <div className="font-medium">{msg.from}</div>
                        <div className="text-sm text-gray-500">{new Date(msg.timestamp).toLocaleString()}</div>
                      </div>
                      <div className="text-sm line-clamp-1">{msg.content}</div>
                    </div>
                  ))}
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="contacts">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="font-medium">Contacts</h3>
                  <Button size="sm" variant="outline">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Contact
                  </Button>
                </div>
                
                <div className="border rounded-lg p-4 h-96 overflow-y-auto">
                  {contacts?.map(contact => (
                    <div key={contact.id} className="p-2 border-b last:border-b-0 hover:bg-secondary/50 cursor-pointer">
                      <div className="font-medium">{contact.name}</div>
                      <div className="text-sm text-gray-500">{contact.email}</div>
                      <div className="text-xs text-gray-400">Last contact: {new Date(contact.lastContact).toLocaleString()}</div>
                    </div>
                  ))}
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default CommunicationHub;