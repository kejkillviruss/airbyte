import { faSlack } from "@fortawesome/free-brands-svg-icons/faSlack";
import { faEnvelope } from "@fortawesome/free-regular-svg-icons";
import { faQuestionCircle } from "@fortawesome/free-regular-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import classNames from "classnames";
import React from "react";
import { FormattedMessage, FormattedNumber } from "react-intl";
import { NavLink } from "react-router-dom";

import { Link } from "components";
import { CreditsIcon } from "components/icons/CreditsIcon";
import { DropdownMenu, DropdownMenuItemType } from "components/ui/DropdownMenu";
import { Text } from "components/ui/Text";

import { useExperiment } from "hooks/services/Experiment";
import { FeatureItem, IfFeatureEnabled } from "hooks/services/Feature";
import { useCurrentWorkspace } from "hooks/services/useWorkspace";
import { CloudRoutes } from "packages/cloud/cloudRoutes";
import { useIntercom } from "packages/cloud/services/thirdParty/intercom";
import { useGetCloudWorkspace } from "packages/cloud/services/workspaces/CloudWorkspacesService";
import { WorkspacePopout } from "packages/cloud/views/workspaces/WorkspacePopout";
import { links } from "utils/links";
import ChatIcon from "views/layout/SideBar/components/ChatIcon";
import ConnectionsIcon from "views/layout/SideBar/components/ConnectionsIcon";
import DestinationIcon from "views/layout/SideBar/components/DestinationIcon";
import DocsIcon from "views/layout/SideBar/components/DocsIcon";
import OnboardingIcon from "views/layout/SideBar/components/OnboardingIcon";
import RecipesIcon from "views/layout/SideBar/components/RecipesIcon";
import SettingsIcon from "views/layout/SideBar/components/SettingsIcon";
import SourceIcon from "views/layout/SideBar/components/SourceIcon";
import StatusIcon from "views/layout/SideBar/components/StatusIcon";
import { NotificationIndicator } from "views/layout/SideBar/NotificationIndicator";
import { useCalculateSidebarStyles } from "views/layout/SideBar/SideBar";

import { RoutePaths } from "../../../../../pages/routePaths";
import styles from "./SideBar.module.scss";

const SideBar: React.FC = () => {
  const navLinkClassName = useCalculateSidebarStyles();
  const workspace = useCurrentWorkspace();
  const cloudWorkspace = useGetCloudWorkspace(workspace.workspaceId);
  const { show } = useIntercom();
  const handleChatUs = () => show();
  const hideOnboardingExperiment = useExperiment("onboarding.hideOnboarding", false);

  return (
    <nav className={styles.nav}>
      <div>
        <Link
          to={
            workspace.displaySetupWizard && !hideOnboardingExperiment ? RoutePaths.Onboarding : RoutePaths.Connections
          }
        >
          <img src="/simpleLogo.svg" alt="logo" height={33} width={33} />
        </Link>
        <WorkspacePopout>
          {({ onOpen, value }) => (
            <button className={styles.workspaceButton} onClick={onOpen}>
              {value}
            </button>
          )}
        </WorkspacePopout>
        <ul className={styles.menu}>
          {workspace.displaySetupWizard && !hideOnboardingExperiment ? (
            <li>
              <NavLink className={navLinkClassName} to={RoutePaths.Onboarding}>
                <OnboardingIcon />
                <Text className={styles.text} size="sm">
                  <FormattedMessage id="sidebar.onboarding" />
                </Text>
              </NavLink>
            </li>
          ) : null}
          <li>
            <NavLink className={navLinkClassName} to={RoutePaths.Connections}>
              <ConnectionsIcon />
              <Text className={styles.text} size="sm">
                <FormattedMessage id="sidebar.connections" />
              </Text>
            </NavLink>
          </li>
          <li>
            <NavLink className={navLinkClassName} to={RoutePaths.Source}>
              <SourceIcon />
              <Text className={styles.text} size="sm">
                <FormattedMessage id="sidebar.sources" />
              </Text>
            </NavLink>
          </li>
          <li>
            <NavLink className={navLinkClassName} to={RoutePaths.Destination}>
              <DestinationIcon />
              <Text className={styles.text} size="sm">
                <FormattedMessage id="sidebar.destinations" />
              </Text>
            </NavLink>
          </li>
        </ul>
      </div>
      <ul className={styles.menu}>
        <li>
          <NavLink className={navLinkClassName} to={CloudRoutes.Credits}>
            <CreditsIcon />
            <Text className={styles.text} size="sm">
              <FormattedNumber value={cloudWorkspace.remainingCredits} />
            </Text>
          </NavLink>
        </li>
        <li>
          <DropdownMenu
            placement="right"
            displacement={10}
            options={[
              {
                type: DropdownMenuItemType.LINK,
                href: links.docsLink,
                icon: <DocsIcon />,
                displayName: <FormattedMessage id="sidebar.documentation" />,
              },
              {
                type: DropdownMenuItemType.LINK,
                href: links.slackLink,
                icon: <FontAwesomeIcon icon={faSlack} />,
                displayName: <FormattedMessage id="sidebar.joinSlack" />,
              },
              {
                type: DropdownMenuItemType.LINK,
                href: links.statusLink,
                icon: <StatusIcon />,
                displayName: <FormattedMessage id="sidebar.status" />,
              },
              {
                type: DropdownMenuItemType.LINK,
                href: links.tutorialLink,
                icon: <RecipesIcon />,
                displayName: <FormattedMessage id="sidebar.recipes" />,
              },
            ]}
          >
            {({ open }) => (
              <button className={classNames(styles.dropdownMenuButton, { [styles.open]: open })}>
                <DocsIcon />
                <Text className={styles.text} size="sm">
                  <FormattedMessage id="sidebar.resources" />
                </Text>
              </button>
            )}
          </DropdownMenu>
        </li>
        <li>
          <DropdownMenu
            placement="right"
            displacement={10}
            options={[
              {
                type: DropdownMenuItemType.LINK,
                href: links.supportTicketLink,
                icon: <FontAwesomeIcon icon={faEnvelope} />,
                displayName: <FormattedMessage id="sidebar.supportTicket" />,
              },
              {
                type: DropdownMenuItemType.BUTTON,
                onSelect: handleChatUs,
                icon: <ChatIcon />,
                displayName: <FormattedMessage id="sidebar.chat" />,
              },
            ]}
          >
            {({ open }) => (
              <button className={classNames(styles.dropdownMenuButton, { [styles.open]: open })}>
                <FontAwesomeIcon icon={faQuestionCircle} size="2x" />
                <Text className={styles.text} size="sm">
                  <FormattedMessage id="sidebar.support" />
                </Text>
              </button>
            )}
          </DropdownMenu>
        </li>
        <li>
          <NavLink className={navLinkClassName} to={RoutePaths.Settings}>
            <IfFeatureEnabled feature={FeatureItem.AllowUpdateConnectors}>
              <React.Suspense fallback={null}>
                <NotificationIndicator />
              </React.Suspense>
            </IfFeatureEnabled>
            <SettingsIcon />
            <Text className={styles.text} size="sm">
              <FormattedMessage id="sidebar.settings" />
            </Text>
          </NavLink>
        </li>
      </ul>
    </nav>
  );
};

export default SideBar;
