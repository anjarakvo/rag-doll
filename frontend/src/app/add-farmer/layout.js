import { ChatContextProvider, UserContextProvider } from "@/context";
import { ChatTabs } from "@/components";

const AddFarmerLayout = ({ children }) => {
  return (
    <UserContextProvider>
      <ChatContextProvider>
        {children}
        <ChatTabs />
      </ChatContextProvider>
    </UserContextProvider>
  );
};

export default AddFarmerLayout;
